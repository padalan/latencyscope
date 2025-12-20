import sys
from unittest.mock import MagicMock


# Mock hdrhistogram
class MockHdrHistogram:
    def __init__(self, *args, **kwargs):
        pass

    def record_value(self, value):
        pass

    def get_value_at_percentile(self, percentile):
        return 0

    def get_max_value(self):
        return 0


mock_hdr = MagicMock()
mock_hdr.HdrHistogram = MockHdrHistogram
sys.modules["hdrhistogram"] = mock_hdr

# Mock bcc
mock_bcc = MagicMock()
mock_bcc.BPF = MagicMock()
sys.modules["bcc"] = mock_bcc
