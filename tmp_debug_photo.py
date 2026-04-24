import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()
from django.test.utils import setup_test_environment
setup_test_environment()
# Use a runner that doesn't create a DB if we use keepdb=True and it exists, 
# but the previous error suggests we might not have 'create' perms.
# However, usually there is a test DB already.
from django.test.runner import DiscoverRunner
runner = DiscoverRunner(verbosity=0, keepdb=True)
import hotel.tests.test_rbac_maintenance as m
def debug_test(self):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from unittest import mock
    req = self._make_request()
    from hotel.tests.test_rbac_maintenance import _authed_client, _FAKE_CLOUDINARY_UPLOAD
    c = _authed_client(self.supervisor.user)
    upload = SimpleUploadedFile('x.png', self._png_bytes(), content_type='image/png')
    with mock.patch('cloudinary.uploader.upload', return_value=_FAKE_CLOUDINARY_UPLOAD):
        resp = c.post(f'{self.base}/photos/', data={'request': req.id, 'images': [upload]}, format='multipart')
    print('STATUS:', resp.status_code)
    print('BODY:', resp.content.decode())

m.MaintenanceEndpointEnforcementTest.test_supervisor_cannot_upload_photo_without_upload_cap = debug_test
# Manually setup databases with keepdb=True
old_config = runner.setup_databases()
try:
    import unittest
    suite = unittest.TestSuite()
    # Need an instance to call _make_request and _png_bytes or just use the class
    # Better: use the loader
    test_loader = unittest.TestLoader()
    test_name = 'hotel.tests.test_rbac_maintenance.MaintenanceEndpointEnforcementTest.test_supervisor_cannot_upload_photo_without_upload_cap'
    s = test_loader.loadTestsFromName(test_name)
    unittest.TextTestRunner(verbosity=1).run(s)
finally:
    runner.teardown_databases(old_config)
