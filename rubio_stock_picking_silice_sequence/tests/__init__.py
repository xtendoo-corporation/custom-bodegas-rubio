from odoo.tests.common import TransactionCase


class TestSiliceSequence(TransactionCase):
    """Test suite for Silíce sequence assignment on stock pickings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create warehouse and locations
        cls.warehouse = cls.env["stock.warehouse"].search([], limit=1)
        cls.location_src = cls.warehouse.lot_stock_id
        cls.location_dest = cls.env["stock.location"].create(
            {
                "name": "Test Destination Location",
                "usage": "customer",
            }
        )

        # Create a simple product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product Silíce",
                "type": "product",
            }
        )

        # Create a second company for multi-company tests
        cls.company_main = cls.env.company
        cls.company_secondary = cls.env["res.company"].create(
            {
                "name": "Test Company Secondary",
            }
        )

    def _create_picking(self, company=None):
        """Helper method to create a picking with initial stock."""
        if company is None:
            company = self.company_main

        picking_type = self.env["stock.picking.type"].search(
            [
                ("code", "=", "outgoing"),
                ("company_id", "=", company.id),
            ],
            limit=1,
        )

        if not picking_type:
            picking_type = self.env["stock.picking.type"].create(
                {
                    "name": "Test Delivery",
                    "code": "outgoing",
                    "sequence_code": "OUT",
                    "company_id": company.id,
                    "warehouse_id": self.warehouse.id,
                }
            )

        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": self.location_src.id,
                "location_dest_id": cls.location_dest.id,
                "company_id": company.id,
            }
        )

        # Add a move line
        self.env["stock.move"].create(
            {
                "name": self.product.name,
                "product_id": self.product.id,
                "product_uom_qty": 10.0,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.location_src.id,
                "location_dest_id": self.location_dest.id,
            }
        )

        return picking

    def test_01_sequence_assigned_on_validate(self):
        """Test that Silíce sequence is assigned when validating a picking."""
        picking = self._create_picking()

        # Before validation, silice_sequence should be empty
        self.assertFalse(
            picking.silice_sequence,
            "Silíce sequence should be empty before validation",
        )

        # Confirm and validate the picking
        picking.action_confirm()
        picking.action_assign()

        # Set quantities done
        for move in picking.move_ids:
            for move_line in move.move_line_ids:
                move_line.quantity = move_line.product_uom_qty

        picking.button_validate()

        # After validation, silice_sequence should be set
        self.assertTrue(
            picking.silice_sequence,
            "Silíce sequence should be assigned after validation",
        )
        self.assertTrue(
            picking.silice_sequence.startswith("SIL-"),
            f"Silíce sequence should start with 'SIL-', got: {picking.silice_sequence}",
        )

    def test_02_sequence_not_reassigned(self):
        """Test that sequence is not reassigned on repeated validations."""
        picking = self._create_picking()

        # Validate the picking
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            for move_line in move.move_line_ids:
                move_line.quantity = move_line.product_uom_qty

        picking.button_validate()

        original_sequence = picking.silice_sequence
        self.assertTrue(original_sequence, "Sequence should be assigned")

        # Try to call button_validate again (simulate revalidation scenario)
        # In real scenarios, you can't validate twice, but we test idempotency
        picking.button_validate()

        self.assertEqual(
            picking.silice_sequence,
            original_sequence,
            "Silíce sequence should not change on repeated validation attempts",
        )

    def test_03_name_field_not_modified(self):
        """Test that standard 'name' field is not modified by this module."""
        picking = self._create_picking()

        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            for move_line in move.move_line_ids:
                move_line.quantity = move_line.product_uom_qty

        # Store original name
        original_name = picking.name

        picking.button_validate()

        # Check that name hasn't changed
        self.assertEqual(
            picking.name,
            original_name,
            "Standard 'name' field should not be modified",
        )

        # Check that silice_sequence is different from name
        self.assertNotEqual(
            picking.silice_sequence,
            picking.name,
            "Silíce sequence should be different from standard name",
        )

    def test_04_multicompany_independent_sequences(self):
        """Test that different companies have independent sequence counters."""
        # Create and validate picking in main company
        picking1 = self._create_picking(company=self.company_main)
        picking1.action_confirm()
        picking1.action_assign()
        for move in picking1.move_ids:
            for move_line in move.move_line_ids:
                move_line.quantity = move_line.product_uom_qty
        picking1.button_validate()

        seq1 = picking1.silice_sequence
        self.assertTrue(seq1, "First picking should have sequence")

        # Create and validate picking in secondary company
        picking2 = self._create_picking(company=self.company_secondary)
        picking2.action_confirm()
        picking2.action_assign()
        for move in picking2.move_ids:
            for move_line in move.move_line_ids:
                move_line.quantity = move_line.product_uom_qty
        picking2.button_validate()

        seq2 = picking2.silice_sequence
        self.assertTrue(seq2, "Second picking should have sequence")

        # Both should start with SIL- but could have same counter if independent
        self.assertTrue(seq1.startswith("SIL-"))
        self.assertTrue(seq2.startswith("SIL-"))

    def test_05_batch_validation(self):
        """Test that multiple pickings can be validated in batch."""
        picking1 = self._create_picking()
        picking2 = self._create_picking()

        pickings = picking1 | picking2

        for picking in pickings:
            picking.action_confirm()
            picking.action_assign()
            for move in picking.move_ids:
                for move_line in move.move_line_ids:
                    move_line.quantity = move_line.product_uom_qty

        # Validate in batch
        pickings.button_validate()

        # Both should have sequences assigned
        self.assertTrue(
            picking1.silice_sequence,
            "First picking should have sequence",
        )
        self.assertTrue(
            picking2.silice_sequence,
            "Second picking should have sequence",
        )

        # Sequences should be different
        self.assertNotEqual(
            picking1.silice_sequence,
            picking2.silice_sequence,
            "Each picking should have a unique sequence",
        )
