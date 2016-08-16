from openerp import fields, models


class ZVP(models.Model):
    _name = 'zvp'

    name = fields.Char()
    partner = fields.Char()
