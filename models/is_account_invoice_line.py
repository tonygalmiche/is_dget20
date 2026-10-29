# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models,fields,api
from openerp.tools.translate import _


class is_account_invoice_line(models.Model):
    _description = "Lignes des factures"
    _name = 'is.account.invoice.line'
    _order='id desc'
    _auto = False

    invoice_id             = fields.Many2one('account.invoice', 'Facture')
    date_invoice           = fields.Date("Date de facturation")

    invoice_line_id        = fields.Many2one('account.invoice.line', "Ligne de facture")
    is_invoice_id          = fields.Many2one('account.invoice', 'Facture liée')

    partner_id             = fields.Many2one('res.partner', 'Client')
    contrat_id             = fields.Many2one('is.dossier.contrat', 'Contrat')
    is_contrat_detail_id   = fields.Many2one('is.dossier.contrat.detail', 'Détail Contrat')

    quantity    = fields.Float("Quantité", digits=(14,4))


    montant1    = fields.Float("Montant 1", digits=(14,4))
    codass1_id  = fields.Many2one('is.dossier.code.assurance', 'Code assurance 1')

    montant2    = fields.Float("Montant 2", digits=(14,4))
    codass2_id  = fields.Many2one('is.dossier.code.assurance', 'Code assurance 2')

    montant3    = fields.Float("Montant 3", digits=(14,4))
    codass3_id  = fields.Many2one('is.dossier.code.assurance', 'Code assurance 3')

    montant4    = fields.Float("Montant 4", digits=(14,4))
    codass4_id  = fields.Many2one('is.dossier.code.assurance', 'Code assurance 4')

    sequence    = fields.Integer("Séquence")

    price_subtotal      = fields.Float("Montant HT"      , digits=(14,2))
    is_montant_revision = fields.Float("Montant révision", digits=(14,4))

    total1      = fields.Float("Total 1", digits=(14,4))
    total2      = fields.Float("Total 2", digits=(14,4))
    total3      = fields.Float("Total 3", digits=(14,4))
    total4      = fields.Float("Total 4", digits=(14,4))
    total_ligne = fields.Float("Total ligne", digits=(14,4))

    rapport1      = fields.Float("Rapport 1"    , digits=(14,4))
    rapport2      = fields.Float("Rapport 2"    , digits=(14,4))
    rapport3      = fields.Float("Rapport 3"    , digits=(14,4))
    rapport4      = fields.Float("Rapport 4"    , digits=(14,4))
    rapport_total = fields.Float("Rapport Total", digits=(14,4))

    revision1     = fields.Float("Montant révisé 1"    , digits=(14,4))
    revision2     = fields.Float("Montant révisé 2"    , digits=(14,4))
    revision3     = fields.Float("Montant révisé 3"    , digits=(14,4))
    revision4     = fields.Float("Montant révisé 4"    , digits=(14,4))



 
    def init(self):
        cr , uid, context = self.env.args
        tools.drop_view_if_exists(cr, 'is_account_invoice_line')
        cr.execute("""
            CREATE OR REPLACE view is_account_invoice_line AS (
                select
                    ail.id,
                    ai.id invoice_id,
                    ai.date_invoice,
                    ai.partner_id,
                    ai.is_montant_revision,
                    ail.id invoice_line_id,

                    idcd.codass1_id,
                    idcd.codass2_id,
                    idcd.codass3_id,
                    idcd.codass4_id,
                    idcd.montant1,
                    idcd.montant2,
                    idcd.montant3,
                    idcd.montant4,
                    ail.sequence,
                    idc.id contrat_id,
                    id.numaff,
                    ail.is_contrat_detail_id,
                    ail.price_subtotal,
                    (ail.quantity-ail.is_deja_facture) quantity,
                    ail.is_invoice_id,

                    (ail.quantity-ail.is_deja_facture)*idcd.montant1 total1,
                    (ail.quantity-ail.is_deja_facture)*idcd.montant2 total2,
                    (ail.quantity-ail.is_deja_facture)*idcd.montant3 total3,
                    (ail.quantity-ail.is_deja_facture)*idcd.montant4 total4,
                    (ail.quantity-ail.is_deja_facture)*(idcd.montant1+idcd.montant2+idcd.montant3+idcd.montant4) total_ligne,



                    (ail.quantity-ail.is_deja_facture)*idcd.montant1/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0) rapport1,
                    (ail.quantity-ail.is_deja_facture)*idcd.montant2/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0) rapport2,
                    (ail.quantity-ail.is_deja_facture)*idcd.montant3/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0) rapport3,
                    (ail.quantity-ail.is_deja_facture)*idcd.montant4/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0) rapport4,

                    (ail.quantity-ail.is_deja_facture)*ail.price_unit/NullIf(ai.is_montant_hors_revision,0) rapport_total,

                    (ail.quantity-ail.is_deja_facture)*idcd.montant1 + ((ail.quantity-ail.is_deja_facture)*idcd.montant1/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0)) * ((ail.quantity-ail.is_deja_facture)*ail.price_unit/NullIf(ai.is_montant_hors_revision,0)) * ai.is_montant_revision revision1,
                    (ail.quantity-ail.is_deja_facture)*idcd.montant2 + ((ail.quantity-ail.is_deja_facture)*idcd.montant2/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0)) * ((ail.quantity-ail.is_deja_facture)*ail.price_unit/NullIf(ai.is_montant_hors_revision,0)) * ai.is_montant_revision revision2,
                    (ail.quantity-ail.is_deja_facture)*idcd.montant3 + ((ail.quantity-ail.is_deja_facture)*idcd.montant3/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0)) * ((ail.quantity-ail.is_deja_facture)*ail.price_unit/NullIf(ai.is_montant_hors_revision,0)) * ai.is_montant_revision revision3,
                    (ail.quantity-ail.is_deja_facture)*idcd.montant4 + ((ail.quantity-ail.is_deja_facture)*idcd.montant4/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0)) * ((ail.quantity-ail.is_deja_facture)*ail.price_unit/NullIf(ai.is_montant_hors_revision,0)) * ai.is_montant_revision revision4





                from account_invoice ai join account_invoice_line            ail on ai.id=ail.invoice_id 
                                        join res_partner                      rp on ai.partner_id=rp.id
                                        left join is_dossier_contrat         idc on ai.is_contrat_id=idc.id
                                        left join is_dossier_contrat_detail idcd on ail.is_contrat_detail_id=idcd.id
                                        left join is_dossier                  id on idc.dossier_id=id.id
                where ai.state not in ('draft','cancel')
            )
        """)

        # SQL="""
        #     select 
        #     from account_invoice_line ail inner join account_invoice             ai on ail.invoice_id=ai.id
        #                                   inner join is_dossier_contrat         idc on ai.is_contrat_id=idc.id
        #                                   inner join is_dossier_contrat_detail idcd on ail.is_contrat_detail_id=idcd.id
        #                                   inner join res_partner                 rp on ai.partner_id=rp.id
        #                                   inner join is_dossier                  id on idc.dossier_id=id.id
        #     where 
        #         ai.date_invoice>='"""+str(obj.name)+"""-01-01' and
        #         ai.date_invoice<='"""+str(obj.name)+"""-12-31'
        #     order by ai.name,ail.sequence
        # """

