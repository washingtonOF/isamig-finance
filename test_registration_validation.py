import unittest
from registration_validation import normalize_cpf, resolve_registration

class RegistrationTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(normalize_cpf("529.982.247-25"), "52998224725")
        self.assertIsNone(normalize_cpf("11111111111"))
        self.assertIsNone(normalize_cpf("52998224726"))

    def test_match(self):
        self.assertEqual(resolve_registration("52998224725", {"101": {"cpf": "529.982.247-25", "responsible": "Pessoa Exemplo"}}),
                         {"status": "matched", "unit": "101", "masked_name": "Pessoa ****"})

    def test_ambiguity(self):
        data = {"cpf": "52998224725", "responsible": "Pessoa Exemplo"}
        self.assertEqual(resolve_registration("52998224725", {"101": data, "102": data}), {"status": "review"})
        self.assertEqual(resolve_registration("52998224725", {"204": data}), {"status": "review"})

    def test_missing(self):
        self.assertEqual(resolve_registration("52998224725", {}), {"status": "not_found"})

if __name__ == "__main__":
    unittest.main()
