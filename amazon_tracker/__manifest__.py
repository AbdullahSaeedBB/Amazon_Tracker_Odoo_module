{
    'name': 'Amazon Tracker',
    'version': '1.0',
    'author': 'Abdullah Saeed',
    'summary': 'To tracke amazon products.',
    'description': """
    The Amazon Product Tracking module, is a powerful tool that can help you to improve the efficiency and accuracy of your Amazon business.""",
    'depends': ['base', 'mail'],
    'data': [
        "security/ir.model.access.csv",
        "wizard/generate_product.xml",
        "views/products.xml",
        "views/menu_items.xml",
        "report/product_data_template.xml",
        "report/reports.xml",
    ],
    'images': ['static/description/bannar.gif'],
    'application': True,
    'license': 'LGPL-3',
}
