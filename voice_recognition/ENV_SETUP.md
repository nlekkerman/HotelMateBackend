# Environment Configuration for Voice Recognition

## Required Environment Variables

Add to your `.env` file:

```bash
# OpenAI API Key for Whisper transcription
OPENAI_API_KEY=sk-your-actual-api-key-here
```

## Getting an OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. Add to `.env` file

## Verifying Setup

### Check if key is loaded:

```python
# Django shell
python manage.py shell

>>> from django.conf import settings
>>> print(settings.OPENAI_API_KEY)
# Should print your key (or error if not set)
```

### Test transcription:

```python
# Django shell
python manage.py shell

>>> from voice_recognition.transcription import transcribe_audio
>>> # Upload a test audio file through Django FileField
>>> # transcribe_audio(audio_file)
```

## Settings Configuration

In `settings.py`, ensure the environment variable is loaded:

```python
# Using django-environ (recommended)
import environ
env = environ.Env()

OPENAI_API_KEY = env('OPENAI_API_KEY', default='')

# OR using python-decouple
from decouple import config

OPENAI_API_KEY = config('OPENAI_API_KEY', default='')

# OR using os.environ
import os

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
```

## Security Notes

⚠️ **IMPORTANT**:
- Never commit `.env` file to git
- Never hardcode API keys in source code
- Add `.env` to `.gitignore`
- Use different keys for dev/staging/production
- Rotate keys regularly for security

## API Usage & Costs

OpenAI Whisper API pricing (as of 2025):
- **$0.006 per minute** of audio transcribed
- Example: 10 second voice command = ~$0.001

Average voice command costs:
- 5-10 seconds = $0.0005 - $0.001
- 100 voice commands/day = ~$0.05 - $0.10/day
- 3000 voice commands/month = ~$1.50 - $3.00/month

## Troubleshooting

### Error: "OpenAI package not installed"

```bash
pip install openai>=1.0.0
```

### Error: "OpenAI API configuration error"

Check:
1. `OPENAI_API_KEY` is set in `.env`
2. Key is valid (starts with `sk-`)
3. Key has not expired
4. Account has available credits

### Error: "Audio transcription failed"

Possible causes:
1. Invalid API key
2. No internet connection
3. OpenAI API is down
4. Rate limit exceeded
5. Audio format not supported

Check OpenAI status: https://status.openai.com/
