import unittest
from unittest.mock import MagicMock
from registration_contacts import apply_contacts

class ContactTests(unittest.TestCase):
    def setup_case(self):
        db, tx = MagicMock(), MagicMock()
        records = {
            "registration_claims": {"cpf":"52998224725","phone":"85999990000","email":"test@example.com","whatsapp":True},
            "registration_decisions": {"decision":"approved","unit":"302","decidedBy":"master"},
            "users": {"status":"approved","unit":"302","email":"test@example.com"},
            "residents": {"cpf":"52998224725","phone":"8500000000"},
            "resident_contact_preferences": {},
        }
        refs = {}
        for name in list(records)+["registration_contact_audit"]:
            ref = MagicMock()
            ref.get.return_value.exists = name in records
            ref.get.return_value.to_dict.side_effect = lambda n=name: records.get(n)
            refs[name] = ref
        db.collection.side_effect = lambda name: MagicMock(document=MagicMock(return_value=refs[name]))
        return db, tx, records, refs

    def invoke(self, db, tx):
        return apply_contacts.to_wrap(tx, db, "test-user")

    def test_approved(self):
        db, tx, records, refs = self.setup_case()
        self.assertEqual(self.invoke(db, tx), "applied")
        tx.update.assert_called_once()
        tx.create.assert_called_once()
        tx.set.assert_called_once()

    def test_rejected(self):
        db, tx, records, refs = self.setup_case()
        records["registration_decisions"]["decision"] = "rejected"
        self.assertEqual(self.invoke(db, tx), "not_approved")
        tx.update.assert_not_called()

    def test_changed_identity(self):
        db, tx, records, refs = self.setup_case()
        records["residents"]["cpf"] = "11111111111"
        self.assertEqual(self.invoke(db, tx), "identity_changed")
        tx.update.assert_not_called()

    def test_duplicate(self):
        db, tx, records, refs = self.setup_case()
        refs["registration_contact_audit"].get.return_value.exists = True
        self.assertEqual(self.invoke(db, tx), "already_applied")
        tx.update.assert_not_called()

    def test_pending_account(self):
        db, tx, records, refs = self.setup_case()
        records["users"]["status"] = "pending"
        self.assertEqual(self.invoke(db, tx), "access_not_approved")
        tx.update.assert_not_called()
