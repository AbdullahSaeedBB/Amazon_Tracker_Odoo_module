from odoo import models, fields, api, _
from odoo.addons.amazon_tracker import tracker
from base64 import b64decode
from queue import Queue
from io import BytesIO
from PIL import Image


class Amazon(models.Model):
    _name = "amazon.products"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Amazon Products Database"

    # Product data
    asin = fields.Char(string="ASIN", readonly=True)
    image = fields.Image(string="Image", readonly=True)
    name = fields.Char(string="Product", tracking=True, readonly=True)
    short_title = fields.Char(string="Product")
    price = fields.Char(string="Price", tracking=True, readonly=True)
    rating = fields.Float(string="Rating", tracking=True, readonly=True)
    reviews = fields.Integer(string="Reviews", tracking=True, readonly=True)
    status = fields.Char(string="Status", tracking=True, readonly=True)
    seller = fields.Char(string="Sold by", tracking=True, readonly=True)
    Html_info = fields.Html(string="Notes")

    # Product info
    product_datetime = fields.Date('Date added', readonly=True, default=lambda self: fields.Datetime.now(),
                                   help="Date the product was generated in the module.")
    much_update = fields.Integer("Much update", readonly=True, help="Times that product updated.")

    # Go to product page in Amazon
    def go_product_page(self):
        return {
            'name': 'Go to product page',
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'https://www.amazon.com/dp/' + self.asin
        }

    def update_product(self):
        asin = self.asin
        soup = tracker.make_soup(asin)
        product_data = tracker.get_all_data(soup)

        self.much_update += 1
        values = dict()
        # values['much_update'] = self.much_update + 1
        for key, value in product_data.items():
            values[key] = value

        self.env['amazon.products'].browse(self.id).update(values)

    def update_products(self):
        queue = Queue()
        products_num = 0

        for rec in self:
            rec.much_update += 1
            products_num += 1
            queue.put((rec.id, rec.asin))

        products_data = tracker.generate_data_products(queue, products_num)

        for product in products_data:
            id = product.pop('id')
            self.env['amazon.products'].browse(id).update(product)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def open_img(self):
        img_bytes = self.image

        byte_data = b64decode(img_bytes)
        image_data = BytesIO(byte_data)
        img = Image.open(image_data)
        img.show()