# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context

import logging

_logger = logging.getLogger(__name__)


class ProductReplenishDebug(models.TransientModel):
    _name = 'product.replenish.debug'
    _description = 'Product Replenish Debug'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_tmpl_id = fields.Many2one('product.template', String='Product Template', required=True)
    product_has_variants = fields.Boolean('Has variants', default=False, required=True)
    product_uom_category_id = fields.Many2one('uom.category', related='product_id.uom_id.category_id', readonly=True, required=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unity of measure', required=True)
    quantity = fields.Float('Quantity', default=1, required=True)
    date_planned = fields.Datetime('Scheduled Date', help="Date at which the replenishment should take place.")
 
    route_ids = fields.Many2many('stock.location.route', string='Preferred Routes',
        help="Apply specific route(s) for the replenishment instead of product's default routes.")
    location_id = fields.Many2one('stock.location', string='Location', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    def _compute_warehouse(self):
        for record in self:
            record.warehouse_id = record.location_id.get_warehouse()
            _logger.debug(record.warehouse_id )

            
    @api.onchange('location_id')
    def onchange_location_id(self):
        _logger.debug(self.warehouse_id )
        new_warehouse_id = self.location_id.get_warehouse()
        _logger.debug(new_warehouse_id )
        self.warehouse_id= new_warehouse_id

            
    @api.model
    def default_get(self, fields):
        res = super(ProductReplenishDebug, self).default_get(fields)
        company_user = self.env.user.company_id
        #warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        product_tmpl_id = False
        if 'product_id' in fields:
            if self.env.context.get('default_product_id'):
                product_id = self.env['product.product'].browse(self.env.context['default_product_id'])
                product_tmpl_id = product_id.product_tmpl_id
                res['product_tmpl_id'] = product_id.product_tmpl_id.id
                res['product_id'] = product_id.id
            elif self.env.context.get('default_product_tmpl_id'):
                product_tmpl_id = self.env['product.template'].browse(self.env.context['default_product_tmpl_id'])
                res['product_tmpl_id'] = product_tmpl_id.id
                res['product_id'] = product_tmpl_id.product_variant_id.id
                if len(product_tmpl_id.product_variant_ids) > 1:
                    res['product_has_variants'] = True 
        if 'product_uom_id' in fields:
            res['product_uom_id'] = product_tmpl_id.uom_id.id
        #if 'warehouse_id' in fields:
        #    res['warehouse_id'] = warehouse.id
        if 'date_planned' in fields:
            res['date_planned'] = datetime.datetime.now()
        return res


    def _prepare_run_values(self):
        replenishment = self.env['procurement.group'].create({
            'partner_id': self.product_id.responsible_id.partner_id.id,
        })

        values = {
            'warehouse_id': self.warehouse_id,
            'route_ids': self.route_ids,
            'date_planned': self.date_planned,
            'group_id': replenishment,
        }
        return values
