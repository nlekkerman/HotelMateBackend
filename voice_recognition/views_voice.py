"""Django REST views for the voice command pipeline."""

import logging
from typing import Optional

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from hotel.models import Hotel
from stock_tracker.models import (
    StockItem,
    StockMovement,
    StockPeriod,
    Stocktake,
    StocktakeLine,
)

from .fuzzy_matcher import find_best_match_in_stocktake
from .voice_command_service import VoiceCommandError, process_audio_command

logger = logging.getLogger(__name__)


def _build_match_payload(match: Optional[dict]) -> Optional[dict]:
    if not match:
        return None
    item = match.get("item")
    if not item:
        return None
    return {
        "item_id": item.id,
        "sku": item.sku,
        "name": item.name,
        "confidence": match.get("confidence"),
        "source": match.get("source", "fuzzy"),
    }


class VoiceCommandView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, hotel_identifier):
        audio_file = request.FILES.get("audio")
        stocktake_id = request.data.get("stocktake_id")

        if not audio_file:
            return Response(
                {"success": False, "error": "No audio file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not stocktake_id:
            return Response(
                {"success": False, "error": "No stocktake_id provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_size = 10 * 1024 * 1024
        if audio_file.size > max_size:
            return Response(
                {
                    "success": False,
                    "error": (
                        "Audio file too large (max "
                        f"{max_size // (1024 * 1024)}MB)"
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier),
        )
        stocktake = get_object_or_404(
            Stocktake,
            id=stocktake_id,
            hotel=hotel,
        )

        if stocktake.status == "APPROVED":
            return Response(
                {"success": False, "error": "Stocktake is locked (approved)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            "Voice command request: user=%s hotel=%s stocktake=%s size=%s",
            request.user.username,
            hotel_identifier,
            stocktake_id,
            audio_file.size,
        )

        try:
            result = process_audio_command(
                audio_file,
                stocktake=stocktake,
                min_match_score=getattr(
                    settings,
                    "VOICE_COMMAND_MIN_SCORE",
                    0.55,
                ),
                use_llm=getattr(settings, "VOICE_COMMAND_USE_LLM", False),
                domain_hint=getattr(
                    settings,
                    "VOICE_COMMAND_DOMAIN_HINT",
                    None,
                ),
            )
        except VoiceCommandError as exc:
            logger.warning("Voice command pipeline failed: %s", exc)
            return Response(
                {"success": False, "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        match_payload = _build_match_payload(result.get("match"))
        command_payload = result.get("command", {}).copy()
        command_payload["transcription"] = result.get("cleaned_transcription")

        return Response(
            {
                "success": True,
                "command": command_payload,
                "stocktake_id": int(stocktake_id),
                "raw_transcription": result.get("transcription"),
                "unit_details": result.get("unit_details"),
                "match": match_payload,
            },
            status=status.HTTP_200_OK,
        )


class VoiceCommandConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, hotel_identifier):
        stocktake_id = request.data.get("stocktake_id")
        command = request.data.get("command") or {}

        if not stocktake_id or not command:
            return Response(
                {"success": False, "error": "Missing stocktake_id or command"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier),
        )
        stocktake = get_object_or_404(
            Stocktake,
            id=stocktake_id,
            hotel=hotel,
        )

        if stocktake.status == "APPROVED":
            return Response(
                {"success": False, "error": "Stocktake is locked (approved)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item_identifier = (command.get("item_identifier") or "").strip()
        if not item_identifier:
            return Response(
                {"success": False, "error": "Command missing item identifier"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        match_result = find_best_match_in_stocktake(
            item_identifier,
            stocktake,
            min_score=getattr(settings, "VOICE_COMMAND_MIN_SCORE", 0.7),
        )

        if match_result:
            stock_item = match_result["item"]
        else:
            stock_item = StockItem.objects.filter(
                hotel=hotel,
                active=True,
            ).filter(
                Q(sku__iexact=item_identifier)
                | Q(name__iexact=item_identifier)
                | Q(sku__icontains=item_identifier)
                | Q(name__icontains=item_identifier)
            ).first()

        if not stock_item:
            return Response(
                {
                    "success": False,
                    "error": (
                        "No matching item found for '"
                        f"{item_identifier}'."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        line, created = StocktakeLine.objects.get_or_create(
            stocktake=stocktake,
            item=stock_item,
            defaults={
                "opening_qty": stock_item.total_stock_in_servings,
                "valuation_cost": stock_item.cost_per_serving,
                "purchases": 0,
                "waste": 0,
                "transfers_in": 0,
                "transfers_out": 0,
                "adjustments": 0,
            },
        )

        action = command.get("action")
        value = command.get("value", 0)
        full_units = command.get("full_units")
        partial_units = command.get("partial_units")

        logger.info(
            "Confirm voice command: action=%s item=%s value=%s "
            "full=%s partial=%s",
            action,
            stock_item.sku,
            value,
            full_units,
            partial_units,
        )

        if action == "count":
            if full_units is not None and partial_units is not None:
                line.counted_full_units = full_units
                line.counted_partial_units = partial_units
            else:
                line.counted_full_units = value
                line.counted_partial_units = 0
            line.save()
            message = f"Counted {stock_item.name}"

        elif action in {"purchase", "waste"}:
            try:
                message = self._apply_movement(
                    request,
                    stocktake,
                    stock_item,
                    action,
                    value,
                )
            except VoiceCommandError as exc:
                return Response(
                    {"success": False, "error": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            line.refresh_from_db()
        else:
            return Response(
                {"success": False, "error": f"Unknown action '{action}'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from stock_tracker.stock_serializers import StocktakeLineSerializer

        serializer = StocktakeLineSerializer(line)

        from stock_tracker.pusher_utils import broadcast_line_counted_updated

        try:
            broadcast_line_counted_updated(
                hotel_identifier,
                stocktake.id,
                {
                    "line_id": line.id,
                    "item_sku": stock_item.sku,
                    "line": serializer.data,
                },
            )
        except Exception as exc:
            logger.warning("Pusher broadcast failed: %s", exc)

        return Response(
            {
                "success": True,
                "line": serializer.data,
                "message": message,
                "item_name": stock_item.name,
                "item_sku": stock_item.sku,
            },
            status=status.HTTP_200_OK,
        )

    def _apply_movement(
        self,
        request,
        stocktake,
        stock_item,
        action: str,
        value,
    ) -> str:
        from decimal import Decimal
        from datetime import datetime, time

        from django.utils import timezone

        quantity_decimal = Decimal(str(value))
        category = stock_item.category_id
        uom = stock_item.uom

        if action == "purchase":
            if uom == Decimal("1"):
                if quantity_decimal % 1 != 0:
                    unit_name = self._unit_name(category, stock_item)
                    raise VoiceCommandError(
                        f"Purchases must be full {unit_name} only."
                    )
            else:
                if quantity_decimal % 1 != 0:
                    unit_name = self._unit_name(
                        category,
                        stock_item,
                        plural=True,
                    )
                    raise VoiceCommandError(
                        f"Purchases must be in full {unit_name}."
                    )
                quantity_decimal = quantity_decimal * uom
        else:  # waste
            if uom == Decimal("1"):
                if quantity_decimal >= 1:
                    unit_name = self._unit_name(category, stock_item)
                    raise VoiceCommandError(
                        f"Waste must be partial {unit_name} only."
                    )
            else:
                if quantity_decimal >= uom:
                    unit_name = self._unit_name(
                        category,
                        stock_item,
                        plural=True,
                    )
                    raise VoiceCommandError(
                        f"Waste must be partial {unit_name}."
                    )

        period = StockPeriod.objects.filter(
            hotel=stocktake.hotel,
            start_date=stocktake.period_start,
            end_date=stocktake.period_end,
        ).first()

        movement_timestamp = timezone.now()
        period_end_dt = timezone.make_aware(
            datetime.combine(stocktake.period_end, time.max)
        )
        if movement_timestamp > period_end_dt:
            movement_timestamp = period_end_dt

        staff_user = getattr(request.user, "staff", None)

        movement_type = "PURCHASE" if action == "purchase" else "WASTE"
        movement = StockMovement.objects.create(
            hotel=stocktake.hotel,
            item=stock_item,
            period=period,
            movement_type=movement_type,
            quantity=quantity_decimal,
            unit_cost=stock_item.unit_cost,
            reference=f"Voice-Stocktake-{stocktake.id}",
            notes=f"Voice command: {action} {value}",
            staff=staff_user,
        )
        movement.timestamp = movement_timestamp
        movement.save(update_fields=["timestamp"])

        from stock_tracker.stocktake_service import _calculate_period_movements

        movements = _calculate_period_movements(
            stock_item,
            stocktake.period_start,
            stocktake.period_end,
        )

        line = StocktakeLine.objects.get(stocktake=stocktake, item=stock_item)
        line.purchases = movements["purchases"]
        line.waste = movements["waste"]
        line.save(update_fields=["purchases", "waste"])

        if action == "purchase":
            return f"Recorded purchase for {stock_item.name}"
        return f"Recorded waste for {stock_item.name}"

    def _unit_name(self, category, stock_item, plural: bool = False) -> str:
        if category == "M" and stock_item.subcategory == "SYRUPS":
            return "bottles" if plural else "bottle"
        if category == "M":
            return "boxes" if plural else "box"
        if category in {"S", "W"}:
            return "bottles" if plural else "bottle"
        if category == "D":
            return "kegs" if plural else "keg"
        return "units" if plural else "unit"
