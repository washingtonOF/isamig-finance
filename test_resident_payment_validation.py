import binascii
import unittest
from resident_payment_validation import valid_pix

def tlv(tag, value):
    return tag + f"{len(value):02d}" + value

def sample(currency="986", country="BR", gui="br.gov.bcb.pix"):
    payload = ("000201" + tlv("26", tlv("00", gui) + tlv("01", "synthetic-test"))
               + tlv("53", currency) + tlv("58", country) + "6304")
    return payload + f"{binascii.crc_hqx(payload.encode('ascii'), 0xffff):04X}"

class PixValidationTests(unittest.TestCase):
    def test_valid_synthetic(self):
        self.assertTrue(valid_pix(sample()))
    def test_corruption(self):
        code = sample()
        self.assertFalse(valid_pix(code.replace("synthetic-test", "synthetic-best")))
    def test_wrong_currency(self):
        self.assertFalse(valid_pix(sample(currency="840")))
    def test_wrong_country(self):
        self.assertFalse(valid_pix(sample(country="US")))
    def test_wrong_gui(self):
        self.assertFalse(valid_pix(sample(gui="example.invalid")))
    def test_invalid_input(self):
        for value in (None, 123, "", "000201", sample()[:-1], "x"*1025):
            self.assertFalse(valid_pix(value))

if __name__ == "__main__":
    unittest.main()
