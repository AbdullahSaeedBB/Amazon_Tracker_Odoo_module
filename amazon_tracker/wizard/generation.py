from odoo.addons.amazon_tracker import tracker
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from queue import Queue

queue = Queue()


###############################################
# B0BSKX9V7C B012CZ41ZA B0BSVRC9K1 B0BYSG72M6 #
# B07BBG487T B083G2MNMS B071CV8CG2 B0BP3ZK9K9 #
# B09SQ3XYS2 B07CSWQR3V B07JMNNPXC B07PQTSRSH #
###############################################


class GenerateProduct(models.TransientModel):
    _name = "generate.product"
    _description = "Generate product by barcode"

    barcode = fields.Char(string="ASIN")
    all_barcodes = fields.Text(string="", readonly=True)

    length = fields.Integer("Length: ", readonly=True)

    # Adding asin to group of asins
    def add_asin(self):
        all_asins = self.all_barcodes
        asin = self.barcode
        if not asin:
            raise ValidationError(
                _("There is no ASIN. You have to enter the ASIN of the product and then click the '+' button."))

        if len(asin) != 10:
            raise ValidationError(
                _(f"'{asin}' This is a wrong ASIN, Check this ASIN you have entered."))

        queue.put(asin)

        self.length += 1

        if not all_asins:
            asins = f"   {asin}\n"
        else:
            asins = f"{all_asins}   {asin}\n"  # all_asins + asin + "\n"

        self.barcode = None
        self.all_barcodes = asins

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'generate.product',
            'target': 'new',
            'res_id': self.id
        }

    def clear_asins(self):
        global queue
        queue = Queue()
        self.all_barcodes = None
        self.length = 0

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'generate.product',
            'target': 'new',
            'res_id': self.id
        }

    def generating(self):
        if not self.all_barcodes:
            raise ValidationError(
                _("There is no asins to generate."))

        asins = self.all_barcodes.split()

        products = tracker.generate_data_products(queue, len(asins))

        bad_asin = list()
        for product in products:
            try:
                product['name']
                self.env['amazon.products'].create(product)

            except:
                bad_asin.append(product['asin'])

        # If there is a not exist ASIN in ASINs group, send a message to user about them
        if bad_asin:
            msg = "Hello ✋. These ASINS not exist, be sure about them:"
            for asin in bad_asin:
                msg += f"\n  {asin}"
            raise ValidationError(_(msg))

        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
