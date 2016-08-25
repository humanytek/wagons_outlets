from openerp import _, api, exceptions, fields, models


class WagonsOutlets(models.Model):
    _name = 'wagons.outlets'
    _inherit = ['mail.thread']

    name = fields.Char()

    state = fields.Selection([
        ('capture', 'Capture'),
        ('load', 'Load'),
        ('analysis', 'Analysis'),
        ('done', 'Done'),
    ], default='capture')

    contract_id = fields.Many2one('sale.order')
    contract_type = fields.Selection(readonly=True, related="contract_id.contract_type")
    partner_id = fields.Many2one('res.partner', related="contract_id.partner_id", readonly=True)
    street = fields.Char(readonly=True, related='partner_id.street')

    wagon = fields.Char()
    zvp_id = fields.Many2one('zvp')
    zvp_partner = fields.Char(related="zvp_id.partner", readonly=True)
    seal_down_from = fields.Char()
    seal_down_to = fields.Char()

    hired = fields.Float(readonly=True, compute="_compute_hired", store=False)
    delivered = fields.Float(readonly=True, compute="_compute_delivered", store=False)
    pending = fields.Float(readonly=True, compute="_compute_pending", store=False)

    product_id = fields.Many2one('product.product', compute="_compute_product_id", store=False, readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', related="contract_id.warehouse_id", readonly=True)

    humidity = fields.Float(min_value=0)
    density = fields.Float(min_value=0)
    temperature = fields.Float(min_value=0)

    damaged = fields.Float(min_value=0, max_value=10)
    broken = fields.Float(min_value=0)
    impurities = fields.Float(min_value=0)

    transgenic = fields.Float(min_value=0)
    seal_up_from = fields.Char()
    seal_up_to = fields.Char()

    ticket = fields.Char()


    weight_1 = fields.Float(min_value=0)
    weight_2 = fields.Float(min_value=0)
    weight_3 = fields.Float(min_value=0)
    weight_4 = fields.Float(min_value=0)
    weight_neto = fields.Float(compute="_compute_weight_neto", store=False)

    kilos_damaged = fields.Float(compute="_compute_kilos_damaged", store=False)
    kilos_broken = fields.Float(compute="_compute_kilos_broken", store=False)
    kilos_impurities = fields.Float(compute="_compute_kilos_impurities", store=False)
    kilos_humidity = fields.Float(compute="_compute_kilos_humidity", store=False)
    weight_neto_analized = fields.Float(compute="_compute_weight_neto_analized", store=False)

    stock_picking = fields.Many2one('stock.picking', readonly=True)

    _defaults = {'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'reg_code'), }

    @api.one
    @api.depends('weight_1', 'weight_2', 'weight_3', 'weight_4')
    def _compute_weight_neto(self):
        self.weight_neto = self.weight_1 + self.weight_2 + self.weight_3 + self.weight_4

    @api.one
    @api.depends('weight_neto', 'damaged')
    def _compute_kilos_damaged(self):
        if self.damaged > 5:
            self.kilos_damaged = ((self.damaged - 5) / 100) * self.weight_neto
        else:
            self.kilos_damaged = 0

    @api.one
    @api.depends('weight_neto', 'broken')
    def _compute_kilos_broken(self):
        if self.broken > 2:
            self.kilos_broken = ((self.broken - 2) / 100) * self.weight_neto
        else:
            self.kilos_broken = 0

    @api.one
    @api.depends('weight_neto', 'impurities')
    def _compute_kilos_impurities(self):
        if self.impurities > 2:
            self.kilos_impurities = ((self.impurities - 2) / 100) * self.weight_neto
        else:
            self.kilos_impurities = 0

    @api.one
    @api.depends('weight_neto', 'humidity')
    def _compute_kilos_humidity(self):
        if self.humidity > 14:
            self.kilos_humidity = ((self.humidity - 14) * .0116) * self.weight_neto
        else:
            self.kilos_humidity = 0

    @api.one
    @api.depends('weight_neto', 'kilos_damaged', 'kilos_broken', 'kilos_impurities', 'kilos_humidity')
    def _compute_weight_neto_analized(self):
        self.weight_neto_analized = self.weight_neto - self.kilos_damaged - self.kilos_broken - self.kilos_impurities - self.kilos_humidity

    @api.one
    @api.depends('contract_id')
    def _compute_hired(self):
        self.hired = sum(line.product_uom_qty for line in self.contract_id.order_line)

    @api.one
    @api.depends('contract_id', 'weight_neto')
    def _compute_delivered(self):
        self.delivered = sum(record.weight_neto for record in self.contract_id.wagons_outlets_ids) / 1000

    @api.one
    @api.depends('contract_id')
    def _compute_pending(self):
        self.pending = self.hired - self.delivered

    @api.one
    @api.depends('contract_id')
    def _compute_product_id(self):
        product_id = False
        for line in self.contract_id.order_line:
            product_id = line.product_id
            break
        self.product_id = product_id

    @api.one
    def fun_load(self):
        self.state = 'analysis'

    @api.multi
    def write(self, values, context=None):
        res = super(WagonsOutlets, self).write(values)
        if self.state == 'done':
            zxc = 'zxc' # TODO
        return res

    @api.multi
    def write(self, vals, recursive=None):
        if not recursive:
            if self.state == 'capture':
                self.write({'state': 'load'}, 'r')
            elif self.state == 'load':
                self.write({'state': 'analysis'}, 'r')
            elif self.state == 'analysis':
                self.write({'state': 'done'}, 'r')

        res = super(WagonsOutlets, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        vals['state'] = 'weight_input'
        res = super(WagonsOutlets, self).create(vals)
        return res
