# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class IsClassement(models.Model):
    _name = 'is.classement'
    _description = "Classement"
    _order = 'name'

    name = fields.Char("Classement", required=True, index=True)


class IsSpecialite(models.Model):
    _name = 'is.specialite'
    _description = "Spécialité"
    _order = 'name'

    name = fields.Char("Spécialité", required=True, index=True)


class IsClassementFournisseur(models.Model):
    _name = 'is.classement.fournisseur'
    _description = "Classement Fournisseur"
    _order = 'code'
    _rec_names_search = ('code', 'nature')

    code       = fields.Char("Code"         , required=True, index=True)
    nature     = fields.Char("Nature"       , required=True, index=True)
    classement = fields.Integer("Classement", required=True, index=True)


    @api.depends('code', 'nature', 'classement')
    def _compute_display_name(self):
        for obj in self:
            obj.display_name = str(obj.code)+u' {'+str(obj.nature)+u'}{'+str(obj.classement)+u'}'


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_prefixe                   = fields.Char(u"Préfixe")
    is_numero                    = fields.Integer(u"Numéro")
    is_numero_fournisseur        = fields.Integer(u"Numéro Fournisseur")
    is_service                   = fields.Char(u"Service")
    is_contact                   = fields.Char(u"Contact")
    is_specialite_ids            = fields.Many2many('is.specialite', 'res_partner_is_specialite_rel', 'partner_id', 'specialite_id', u'Spécialités')
    is_classement_id             = fields.Many2one('is.classement', "Classement")
    is_classement_principal_id   = fields.Many2one('is.classement.fournisseur', "Classement principal")
    is_classement_secondaire_id  = fields.Many2one('is.classement.fournisseur', "Classement secondaire")
    is_classement_tertiaire_id   = fields.Many2one('is.classement.fournisseur', "Classement tertiaire")
    is_acces_pro_url             = fields.Char(u"Accès pro au Site internet")
    is_acces_pro_login           = fields.Char(u"Login accès pro")
    is_acces_pro_pwd             = fields.Char(u"Mot de passe accès pro")


    # Permet de désactiver le controle de la TVA
    # v20 : contrôle fait par _check_vat (à l'enregistrement de vat), gardé seulement pour la mise en forme du numéro
    def _check_vat(self, validation="error"):
        return super()._check_vat(validation=False)

