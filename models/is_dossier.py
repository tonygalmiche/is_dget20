# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime
from odoo.exceptions import UserError
import base64
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, PatternFill, Font, borders
from openpyxl.styles.borders import Border
from openpyxl.worksheet.page import PageMargins




def _get_prefix_annee():
    annee = date.today().year
    annee = annee-1989
    x = str(date.today())[-5:]
    if x>='04-01':
        annee+=1 # Si 1er avril, prendre l'année suivante
    return(str(annee))



class IsDossier(models.Model):
    _name = 'is.dossier'
    _description = "Dossier"
    _order = 'numaff desc'
    _rec_name = 'numaff'
    _rec_names_search = ('numaff', 'nom')


    def _get_numaff(self):
        prefix = _get_prefix_annee()+'A'
        dossiers=self.env['is.dossier'].search([('numaff','like',prefix)],order="numaff desc",limit=1)
        numaff=1
        for dossier in dossiers:
            numaff = int(dossier.numaff[-3:])
            numaff+=1
        numaff=prefix+('000'+str(numaff))[-3:]
        return numaff

    numaff               = fields.Char("Dossier", required=True, index=True, default=lambda self: self._get_numaff())
    nom                  = fields.Char("Nom", required=True)
    description_succinte = fields.Text("Description succinte")
    adresse1             = fields.Char("Adresse 1")
    adresse2             = fields.Char("Adresse 2")
    codepostal           = fields.Char("Code postal")
    lieu                 = fields.Char("Ville")
    numconcours          = fields.Char("Numéro de concours")
    m_ouvrage_id         = fields.Many2one('res.partner', "Maitre d'ouvrage", domain=[('is_company','=',True)])
    m_oeuvre_id          = fields.Many2one('res.partner', "Maitre d'oeuvre" , domain=[('is_company','=',True)])
    date                 = fields.Date("Date")
    surface              = fields.Float("Surface")
    montant_ope          = fields.Float("Montant de l'opération")
    site_internet        = fields.Char("Site internet")
    description_complete = fields.Text("Description complète")
    nota                 = fields.Text("Note")
    dossierreference     = fields.Selection([('oui','Oui'),('non','Non')],"Dossier référénce")
    fiche                = fields.Selection([('oui','Oui'),('non','Non')],"Fiche")
    distance             = fields.Float("Distance")
    duree                = fields.Float("Durée")
    service_executant    = fields.Char("Service exécutant", help="Nécessaire pour Chorus Pro")
    num_marche           = fields.Char("N° marché"        , help="Nécessaire pour Chorus Pro")
    note_ids             = fields.One2many('is.dossier.note', 'dossier_id', 'Notes')
    referencee_ids       = fields.Many2many('is.dossier.reference', 'is_dossier_is_reference_rel', 'dossier_id', 'reference_id', 'Références')
    contrat_ids          = fields.One2many('is.dossier.contrat', 'dossier_id', 'Contrats')
    adjudicataire_ids    = fields.One2many('is.dossier.adjudicataire', 'dossier_id', 'Adjudicataires')
    state                = fields.Selection([
            ('en cours' ,'En cours'),
            ('termine'  ,'Terminé'),
            ('abandonne','Abandonné'),
        ],"Etat", default="en cours")

    @api.depends('numaff', 'nom')
    def _compute_display_name(self):
        for obj in self:
            obj.display_name = str(obj.numaff)+' - '+str(obj.nom)


    def creation_contrat_action(self, vals=False):
        for obj in self:
            res= {
                'name': 'Contrat',
                'view_mode': 'form',
                'res_model': 'is.dossier.contrat',
                'type': 'ir.actions.act_window',
                'context': {'default_dossier_id': obj.id }
            }
            return res


class IsDossierAdjudicataire(models.Model):
    _name = 'is.dossier.adjudicataire'
    _description = "Dossier Adjudicataire"
    _order = 'id desc'

    dossier_id       = fields.Many2one('is.dossier', 'Dossier', required=True)
    retenu           = fields.Selection([('oui','Oui'),('non','Non')],"Retenu")
    adjudicataire_id = fields.Many2one('res.partner', "Adjudicataire", index=True)
    montant          = fields.Float("Montant du lot"   , digits=(14,2))
    nomdulot         = fields.Char("Nom du lot")
    notes            = fields.Text("Notes")


class IsDossierNote(models.Model):
    _name = 'is.dossier.note'
    _description = "Dossier Note"
    _order = 'date'
    _rec_name = 'date'

    dossier_id = fields.Many2one('is.dossier', 'Dossier', required=True)
    date       = fields.Date("Date")
    auteur     = fields.Char("Auteur")
    titre      = fields.Char("Titre")
    texte_note = fields.Text("Note")


class IsDossierReference(models.Model):
    _name = 'is.dossier.reference'
    _description = "Référence Dossier"
    _order = 'name'

    name        = fields.Char("Référence dossier", required=True, index=True)
    idreference = fields.Integer("idreference")


class IsDossierContratTraitance(models.Model):
    _name = 'is.dossier.contrat.traitance'
    _description = "Traitance Contrat"
    _order = 'name'

    name   = fields.Char("Traitance", required=True, index=True)
    code   = fields.Char("Code")
    active = fields.Boolean("Active", default=True)


class IsDossierContrat(models.Model):
    _name = 'is.dossier.contrat'
    _description = "Contrat"
    _order = 'name desc'


    @api.depends('detail_ids')
    def compute_restant_ht(self):
        for obj in self:
            restant_ht    = 0
            facturable_ht = 0
            if obj.signe=="oui":
                for line in obj.detail_ids:
                    if line.facturable=="oui":
                        restant_ht += line.montant_ht-line.montant_ht*line.facture_recursif/100.0
                        facturable_ht += line.montant_ht*(line.a_facturer-line.facture_recursif)/100.0
            obj.restant_ht    = restant_ht
            obj.facturable_ht = facturable_ht
        return True

    @api.depends('restant_ht')
    def compute_show_generer_facture_btn(self):
        for obj in self:
            # Masquer le bouton si restant_ht est entre -0.1 et 0.1
            obj.show_generer_facture_btn = not (-0.1 <= obj.facturable_ht <= 0.1)


    @api.depends('detail_ids')
    def compute_numligne_max(self):
        for obj in self:
            numligne_max=0
            for line in obj.detail_ids:
                if line.numligne>numligne_max:
                    numligne_max=line.numligne
            obj.numligne_max=numligne_max


    def _get_numcontrat(self):
        context = self.env.context
        numcontrat=''
        if 'active_id' in context:
            dossier_id = context['active_id']
            dossiers=self.env['is.dossier'].search([('id','=',dossier_id)])
            for dossier in dossiers:
                numaff = dossier.numaff
                prefix = numaff.replace('A','CT')
                dossiers=self.env['is.dossier.contrat'].search([('dossier_id','=',dossier_id)])
                nb = len(dossiers) + 1
                numcontrat = prefix+'-'+str(nb)
        return numcontrat


    name          = fields.Char("Numero de contrat", required=True, index=True, default=lambda self: self._get_numcontrat())
    signe         = fields.Selection([('oui','Oui'),('non','Non')],"Signé")
    dossier_id    = fields.Many2one('is.dossier', "Dossier", index=True, required=True, ondelete='cascade')
    client_id     = fields.Many2one('res.partner', "Client", index=True)
    description   = fields.Char("Description du contrat")
    notes         = fields.Text("Notes")
    condreglement = fields.Text("Condition de règlement")
    delaipaiement = fields.Text("Délai de paiement")
    date          = fields.Date("Date de signature")
    refclient     = fields.Char("N°Commande client", help="Utilisé pour les marchés publiques")
    num_marche    = fields.Char("N°Marché"    , help="Utilisé pour les marchés publiques")
    code_service  = fields.Char("Code service", help="Utilisé pour les marchés publiques")
    traitance_id  = fields.Many2one('is.dossier.contrat.traitance', "Traitance", index=True)
    invoice_ids   = fields.One2many('account.move', 'is_contrat_id', 'Factures', domain=[('state','not in',['cancel'])], readonly=True)
    nb_factures   = fields.Integer("Nombre de factures")
    detail_ids    = fields.One2many('is.dossier.contrat.detail', 'contrat_id', 'Détail')
    restant_ht    = fields.Float("Restant HT"   , digits=(14,2), compute='compute_restant_ht', readonly=True, store=True)
    facturable_ht = fields.Float("Facturable HT", digits=(14,2), compute='compute_restant_ht', readonly=True, store=True)
    heure_ids     = fields.One2many('is.salarie.heure', 'contrat_id', 'Heures', readonly=True)
    tva_id        = fields.Many2one('is.tva', 'TVA')
    anomalie      = fields.Float("Anomalie", default=0)
    state         = fields.Selection([('en_cours','En cours'),('termine','Terminé')],"Etat", default='en_cours')

    numligne_max  = fields.Integer("N° Ligne maxi", compute='compute_numligne_max')
    show_generer_facture_btn = fields.Boolean("Afficher bouton générer facture", compute='compute_show_generer_facture_btn', readonly=True, store=False)


    def update_restant_ht_action(self):
        for obj in self:
            obj.compute_restant_ht()

    def update_reellement_facture_action(self):
        for obj in self:
            obj.update_reellement_facture_contrat(update_facture=True)
            obj.compute_restant_ht()

    def update_reellement_facture_contrat(self, update_facture=False):
        """
        Pour chaque contrat:
        1. Update le nombre de factures dans le contrat
        2. Update le reellement facturé de toutes les factures du contrat (OPTIONNEL)
        3. Update le pourcentage de réellement facturé pour chaque service dans ce contrat
        """
        t_start = datetime.now()
        for obj in self:
            anomalie = 0

            # 1. mettre à jour le nombre de factures dans ce contrat
            obj.nb_factures = len(obj.invoice_ids)

            # 2. met à jour le reellement facturé de toutes les factures
            # (seulement dans le cas de debug où on clique sur "actualiser reellement facture")
            if update_facture:
                obj.invoice_ids.update_deja_facture_action()

            # 3. Pour chaque service, récupérer le pourcentage de déjà facturé dans ce contrat
            # Pour cela: 
            #  3.1. récupérer tous les services et les factures
            #  3.2. mettre à jour le pourcentage de déjà facturé en parcourant chaque service de chaque facture
            factures_recursif = {} 

            # --- 3.1. récupérer tous les services et les factures --- 
            factures = [f for f in obj.invoice_ids if f.state not in ['draft','cancel']]
            services = obj.detail_ids
            # Initialisation du dict de % de déjà facturé
            factures_recursif = { line : 0 for line in services } 
            
             # --- 3.2. maj du % de déjà facturé en parcourant chaque service de chaque facture --- 
            for f in factures:
                # Mettre à jour le reellement facturé pour les services de cette facture
                for line in f.invoice_line_ids:
                    if line.is_contrat_detail_id:
                        # Somme des réellement facturé de chaque facture * le prix
                        signe_line = 1
                        if line.price_unit < 0:
                            signe_line = 1    
                        factures_recursif[line.is_contrat_detail_id] += signe_line*line.is_reellement_facture

            # Le transformer en pourcentage
            for s in services:
                s.facture_recursif = factures_recursif[s]*100
                anomalie += abs(s.facture_recursif - s.a_facturer)*s.montant_ht/100
                    
            obj.anomalie = anomalie
        t_end = datetime.now()

    def acceder_contrat_action(self, vals=False):
        for obj in self:
            res= {
                'name': 'Contrat',
                'view_mode': 'form',
                'res_model': 'is.dossier.contrat',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }
            return res


    def generer_facture_action(self, vals=False):
        for obj in self:

            if not obj.show_generer_facture_btn:
                return


            # mettre à jour le nombre de factures dans ce contrat
            obj.nb_factures = len(obj.invoice_ids)


            #** Recherche du numéro de facture *********************************
            prefix = _get_prefix_annee()+'FC'
            filtre=[
                ('name','like',prefix),
            ]
            invoices = self.env['account.move'].search(filtre,limit=1,order='name desc')
            suffix=1
            for invoice in invoices:
                suffix = int(invoice.name[-3:])+1
            suffix = ('000'+str(suffix))[-3:]
            number  = prefix+suffix
            #*******************************************************************


            #** Création entête facture ****************************************
            invoice_type="out_invoice"
            sens_facture=1
            if obj.facturable_ht<0:
                invoice_type="out_refund"
                sens_facture=-1
            vals={
                'name'              : number,
                'invoice_origin'    : obj.name,
                'partner_id'        : obj.client_id.id,
                'is_contrat_id'     : obj.id,
                'fiscal_position_id': 1,
                'is_tva_id'         : obj.tva_id.id,
                'move_type'         : invoice_type,
                'state'             : 'draft',
            }

            invoice=self.env['account.move'].create(vals)
            invoice_id = invoice.id
            #*******************************************************************

            #** Création lignes du contrat *************************************
            for line in obj.detail_ids:
                if line.commentaire:
                    vals={
                        'move_id'   : invoice_id,
                        'is_contrat_detail_id': line.id,
                        'display_type': 'line_note',
                        'name'      : line.texte,
                        'quantity'  : False,
                        'account_id': False,
                    }
                    invoice_line=self.env['account.move.line'].create(vals)
                else:
                    quantity = line.a_facturer/100.0
                    vals={
                        'move_id'   : invoice_id,
                        'is_contrat_detail_id': line.id,
                        'product_id': 1,
                        'name'      : line.texte,
                        'quantity'  : quantity,
                        'price_unit': False,
                        'account_id': 622, #701100
                    }
                    invoice_line=self.env['account.move.line'].create(vals)
                    line_res = invoice_line.uptate_onchange_product_id()
                    vals={
                        'name'      : line.texte,
                        'price_unit': sens_facture*line.montant_ht,
                    }
                    invoice_line.write(vals)
            #*******************************************************************

            #** Ajout des factures réalisées ***********************************
            filtre=[
                ('is_contrat_id','=',obj.id),
                ('invoice_date','<=',date.today()),
                ('state','not in',['cancel']),
                ('id','!=',invoice_id),
            ]
            factures = self.env['account.move'].search(filtre,order='invoice_date')
            for facture in factures:
                sens_ligne_facture = 1
                if facture.move_type == "out_refund":
                    sens_ligne_facture = -1
                vals={
                    'move_id'      : invoice_id,
                    'product_id'   : 2,
                    'name'         : facture.name,
                    'quantity'     : 1,
                    'price_unit'   : 0,
                    'account_id'   : 622, #701100
                    'is_invoice_id': facture.id,
                }
                invoice_line=self.env['account.move.line'].create(vals)
                line_res = invoice_line.uptate_onchange_product_id()
                vals={
                    'name'      : facture.name,
                    # On veut que le montant final d'une invoice soit positif quelque soit le type d'invoice
                    # Donc on veut que les lignes des invoices précédentes soient en moins si sont type est different
                    # du type de l'invoice donc "-(sens_facture*sens_ligne_facture)"
                    'price_unit'   : -(sens_facture*sens_ligne_facture)*facture.is_montant_hors_revision, # Ceci donne tout bon! 3/3
                }
                invoice_line.write(vals)
            #*******************************************************************

            #** Recalcul de la TVA et validation de la facture *****************
            res_validate = invoice.update_tva_account_action()
            try:
               res_validate = invoice.action_post()
            except:
               continue
            #*******************************************************************

            #*******************************************************************
            invoice.update_deja_facture_action()
            obj.update_reellement_facture_contrat()
            obj.compute_restant_ht()

            res = invoice.acceder_facture_action()
            return res


class IsDossierContratDetail(models.Model):
    _name = 'is.dossier.contrat.detail'
    _description = "Détail Contrat"
    _order = 'contrat_id,numligne,id'
    _rec_name = 'numligne'


    @api.depends('montant1','montant2','montant3','montant4','avancement','a_facturer','facture_recursif')
    def _compute_montant_ht(self):
        for obj in self:
            obj.montant_ht = obj.montant1 + obj.montant2 + obj.montant3 + obj.montant4
            obj.reste_facturable = obj.avancement - obj.facture_recursif


    @api.depends('a_facturer')
    def _compute_facture(self):
        for obj in self:
            obj.montant_a_facturer = obj.montant_ht*(obj.a_facturer-obj.facture_recursif)/100
            obj.montant_facture    = obj.montant_ht*(obj.facture_recursif)/100
            encours=0
            montant_encours=0
            restant=0
            montant_restant=0
            if obj.facturable=='oui':
                if obj.avancement==100:
                    restant=100-obj.facture_recursif
                    montant_restant = restant*obj.montant_ht/100
                else:
                    encours=obj.avancement-obj.facture_recursif
                    montant_encours = encours*obj.montant_ht/100
            obj.encours = encours
            obj.montant_encours = montant_encours
            obj.restant = restant
            obj.montant_restant = montant_restant


    contrat_id  = fields.Many2one('is.dossier.contrat', 'Contrat', required=True, ondelete='cascade')
    state       = fields.Selection(related='contrat_id.state')
    dossier_id  = fields.Many2one(related='contrat_id.dossier_id')
    description = fields.Char(related='contrat_id.description')

    numligne    = fields.Integer("Ligne", default=0)
    commentaire = fields.Boolean("Commentaire", default=False)
    phase_id    = fields.Many2one('is.dossier.contrat.phase', 'Phase')
    det_phase   = fields.Char("Description Phase", related='phase_id.det_phase')

    texte       = fields.Char("Description")
    dateremise  = fields.Date("Date")
    facture_le  = fields.Date("Pour le")

    stxt1       = fields.Char("Description 1")
    montant1    = fields.Float("Montant 1", digits=(14,4))
    codass1_id  = fields.Many2one('is.dossier.code.assurance', 'Code assurance 1')

    stxt2       = fields.Char("Description 2")
    montant2    = fields.Float("Montant 2", digits=(14,4))
    codass2_id  = fields.Many2one('is.dossier.code.assurance', 'Code assurance 2')

    stxt3       = fields.Char("Description 3")
    montant3    = fields.Float("Montant 3", digits=(14,4))
    codass3_id  = fields.Many2one('is.dossier.code.assurance', 'Code assurance 3')

    stxt4       = fields.Char("Description 4")
    montant4    = fields.Float("Montant 4", digits=(14,4))
    codass4_id  = fields.Many2one('is.dossier.code.assurance', 'Code assurance 4')

    montant_ht  = fields.Float("Montant HT", digits=(14,2), compute='_compute_montant_ht', readonly=True, store=True)

    avancement  = fields.Float("% avancement", digits=(14,4))
    nota        = fields.Char("Nota")
    facturable  = fields.Selection([('oui','Oui'),('non','Non')],"Facturable", default='oui')
    a_facturer  = fields.Float("% à facturer", digits=(14,4))
    facture            = fields.Float("% facturé"         , compute='_compute_facture', readonly=True, store=False, digits=(14,4))
    montant_a_facturer = fields.Float("Montant à facturer", compute='_compute_facture', readonly=True, store=False)
    montant_facture    = fields.Float("Montant facturé"   , compute='_compute_facture', readonly=True, store=False)

    facture_recursif   = fields.Float("% facturé récursif", digits=(14,4))

    reste_facturable   = fields.Float("% Reste Facturable", digits=(14,4), compute='_compute_montant_ht', readonly=True, store=True)

    encours                    = fields.Float("% En cours"                , digits=(14,4), compute='_compute_facture', readonly=True, store=False)
    montant_encours            = fields.Float("Montant en cours"          , digits=(14,2), compute='_compute_facture', readonly=True, store=False)
    restant                    = fields.Float("% Restant à facturer"      , digits=(14,4), compute='_compute_facture', readonly=True, store=False)
    montant_restant            = fields.Float("Montant restant à facturer", digits=(14,2), compute='_compute_facture', readonly=True, store=False)


    @api.model_create_multi
    def create(self, vals_list):
        res=super(IsDossierContratDetail, self).create(vals_list)
        for obj in res:
            obj.numligne = obj.contrat_id.numligne_max+10
        return res


    def unlink(self):
        for obj in self:
            lines = self.env['account.move.line'].search([('is_contrat_detail_id','=',obj.id)])
            if len(lines)>0:
                factures=[]
                for line in lines:
                    factures.append(line.move_id.name)
                factures=", ".join(factures)
                raise UserError("Il n'est pas possible de supprimer la ligne '%s' car elle est utilsée dans les factures %s"%(obj.texte,factures))
        return super(IsDossierContratDetail, self).unlink()


class IsDossierContratPhase(models.Model):
    _name = 'is.dossier.contrat.phase'
    _description = "Phase Contrat"
    _order = 'txt_phase'
    _rec_name = 'txt_phase'

    ref_phase       = fields.Integer("Ref"     , required=True, index=True)
    txt_phase       = fields.Char("Code"       , required=True, index=True)
    det_phase       = fields.Char("Description", required=True, index=True)


class IsDossierCodeAssurance(models.Model):
    _name = 'is.dossier.code.assurance'
    _description = "Code Assurance"
    _order = 'ordre,code'
    _rec_name = 'code'

    ordre       = fields.Char("Ordre"      , required=True, index=True, default='x')
    code        = fields.Char("Code"       , required=True, index=True)
    description = fields.Char("Description", required=True, index=True)


class IsSalarieHeure(models.Model):
    _name = 'is.salarie.heure'
    _description = "Heures des salariés"
    _order = 'date_travaillee desc'
    _rec_name = 'date_travaillee'

    date_travaillee = fields.Date("Date travaillée", required=True, index=True, default=lambda *a: fields.Date.today())
    user_id         = fields.Many2one('res.users', 'Utilisateur', required=True, default=lambda self: self.env.user)
    login           = fields.Char("Login")
    contrat_id      = fields.Many2one('is.dossier.contrat', 'Contrat', required=True, ondelete='cascade')
    nb_heures       = fields.Float("Nb heures")
    note            = fields.Char("Note")
    id_heures       = fields.Integer("id_heures", index=True)


class IsDeclarationMAF(models.Model):
    _name = 'is.declaration.maf'
    _description = "Déclaration MAF"

    name          = fields.Char("Année", required=True, index=True)
    type_document = fields.Selection([('maf','Déclaration MAF'),('dget','DGET')],"Type de document", default='maf')

    def getCodeAssurance(self,code_id):
        cr = self.env.cr
        SQL="SELECT code,ordre FROM is_dossier_code_assurance where id="+str(code_id)
        cr.execute(SQL)
        rows = cr.fetchall()
        code='0'
        ordre=''
        for row in rows:
            code  = row[0]
            ordre = row[1]
        return code, ordre


    def get_contrats(self,obj):
        cr = self.env.cr
        SQL="""
            select 
                idcd.codass1_id,
                idcd.codass2_id,
                idcd.codass3_id,
                idcd.codass4_id,
                idcd.montant1,
                idcd.montant2,
                idcd.montant3,
                idcd.montant4,
                ai.name,
                ail.sequence,
                idc.name,
                id.numaff,
                rp.name,
                ail.is_contrat_detail_id,
                ail.price_subtotal,
                (ail.quantity-ail.is_deja_facture),
                ail.is_invoice_id,

                ai.is_montant_revision,

                (ail.quantity-ail.is_deja_facture)*idcd.montant1/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0) rapport1,
                (ail.quantity-ail.is_deja_facture)*idcd.montant2/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0) rapport2,
                (ail.quantity-ail.is_deja_facture)*idcd.montant3/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0) rapport3,
                (ail.quantity-ail.is_deja_facture)*idcd.montant4/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0) rapport4,

                (ail.quantity-ail.is_deja_facture)*ail.price_unit/NullIf(ai.is_montant_hors_revision,0) rapport_total,

                (ail.quantity-ail.is_deja_facture)*idcd.montant1 + ((ail.quantity-ail.is_deja_facture)*idcd.montant1/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0)) * ((ail.quantity-ail.is_deja_facture)*ail.price_unit/NullIf(ai.is_montant_hors_revision,0)) * ai.is_montant_revision revision1,
                (ail.quantity-ail.is_deja_facture)*idcd.montant2 + ((ail.quantity-ail.is_deja_facture)*idcd.montant2/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0)) * ((ail.quantity-ail.is_deja_facture)*ail.price_unit/NullIf(ai.is_montant_hors_revision,0)) * ai.is_montant_revision revision2,
                (ail.quantity-ail.is_deja_facture)*idcd.montant3 + ((ail.quantity-ail.is_deja_facture)*idcd.montant3/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0)) * ((ail.quantity-ail.is_deja_facture)*ail.price_unit/NullIf(ai.is_montant_hors_revision,0)) * ai.is_montant_revision revision3,
                (ail.quantity-ail.is_deja_facture)*idcd.montant4 + ((ail.quantity-ail.is_deja_facture)*idcd.montant4/NullIf(((ail.quantity-ail.is_deja_facture)*ail.price_unit),0)) * ((ail.quantity-ail.is_deja_facture)*ail.price_unit/NullIf(ai.is_montant_hors_revision,0)) * ai.is_montant_revision revision4





            from account_move_line ail inner join account_move                   ai on ail.move_id=ai.id
                                          inner join is_dossier_contrat         idc on ai.is_contrat_id=idc.id
                                          inner join is_dossier_contrat_detail idcd on ail.is_contrat_detail_id=idcd.id
                                          inner join res_partner                 rp on ai.partner_id=rp.id
                                          inner join is_dossier                  id on idc.dossier_id=id.id
            where 
                ai.invoice_date>='"""+str(obj.name)+"""-01-01' and
                ai.invoice_date<='"""+str(obj.name)+"""-12-31' and
                ai.state not in ('draft','cancel')
            order by ai.name,ail.sequence
        """
        cr.execute(SQL)
        rows = cr.fetchall()
        nb=len(rows)
        r={}
        for row in rows:
            contrat = row[10]
            if contrat not in r:
                r[contrat]={}
            qty = row[15]
            if qty:
                if row[0]:
                    if row[0] not in r[contrat]:
                        r[contrat][row[0]]=0
                    r[contrat][row[0]]+=row[23] or 0

                if row[1]:
                    if row[1] not in r[contrat]:
                        r[contrat][row[1]]=0
                    r[contrat][row[1]]+=row[24] or 0

                if row[2]:
                    if row[2] not in r[contrat]:
                        r[contrat][row[2]]=0
                    r[contrat][row[2]]+=row[25] or 0

                if row[3]:
                    if row[3] not in r[contrat]:
                        r[contrat][row[3]]=0
                    r[contrat][row[3]]+=row[26] or 0
                if not row[0] and not row[1] and not row[2] and not row[3]:
                    if 0 not in r[contrat]:
                        r[contrat][0]=0
                    r[contrat][0]+=row[17] or 0
        keys=sorted(r.keys(), reverse=True)
        total=0
        res=[]
        recap={}
        for k in keys:
            lines={}
            for code_id in r[k]:
                montant = r[k][code_id]
                code,ordre = self.getCodeAssurance(code_id)
                if code!="ND":
                    lines[ordre]=[code,montant]
            keys2=sorted(lines.keys(), reverse=False)
            for k2 in keys2:
                line    = lines[k2]
                code    = line[0].strip()
                montant = line[1]
                contrats = self.env['is.dossier.contrat'].search([('name','=',k)],order="name",limit=1)
                if contrats:
                    contrat=contrats[0]
                    traitance = contrat.traitance_id.code or ''
                    cle=code+' - '+traitance
                    if cle not in recap:
                        recap[cle]=0
                    recap[cle]+=montant
                    if montant!=0:
                        vals={
                            'contrat'  : contrat,
                            'code'     : code,
                            'traitance': traitance,
                            'montant'  : montant,
                        }
                        res.append(vals)
                    total+=r[k][code_id]
        keys=sorted(recap.keys(), reverse=False)
        recap2=[]
        for k in keys:
            recap2.append([k,recap[k]])
        return [res,recap2]

    def export_excel_action(self):
        for obj in self:
            res = obj.get_contrats(obj)

            excel_attachment_id = False
            #** Création du workbook ******************************************
            name  = 'declaration-maf-%s.xlsx'%obj.name
            path = '/tmp/%s'%name
            workbook = Workbook()
            ws = workbook.active
            ws.title = "Déclaration MAF"
            ws.sheet_view.showGridLines = False
            border1 = borders.Side(style = None, color = 'FF000000', border_style = 'thin')
            thin_border = Border(left = border1, right = border1, bottom = border1, top = border1)
            #******************************************************************

            #** Ligne d'entête ************************************************
            titres=["N°affaire","N°contrat", "Nom affaire", "Code MAF", "Contrat HT", "Affaire HT"]
            column = 1
            row = 1
            for titre in titres:
                clr_background = PatternFill(start_color='FFFACD', end_color='FFFACD', fill_type="solid")
                cell = ws.cell(row=row, column=column, value=titre)
                cell.fill = clr_background
                cell.alignment = Alignment(horizontal='center')
                cell.font = Font(name='Calibri', bold=True)
                cell.border = thin_border
                column+=1
            #******************************************************************

            #** Largeur des colonnes ******************************************
            ws.column_dimensions['A'].width=12
            ws.column_dimensions['B'].width=15
            ws.column_dimensions['C'].width=40
            ws.column_dimensions['D'].width=12
            ws.column_dimensions['E'].width=15
            ws.column_dimensions['F'].width=15
            #******************************************************************


            #** Totaux des affaires *******************************************
            lines = res[0]
            totaux={}
            for line in lines:
                numaff = line["contrat"].dossier_id.numaff
                if numaff not in totaux:
                    totaux[numaff] = 0
                totaux[numaff]+=line["montant"]
            #******************************************************************


            #** Lignes ********************************************************
            color1 = PatternFill(start_color='DEEBF7', end_color='DEEBF7', fill_type="solid")
            color2 = PatternFill(start_color='D0CECE', end_color='D0CECE', fill_type="solid")
            row+=1
            color=color1
            mem = ""
            first=True
            for line in lines:
                contrat = line["contrat"]
                if mem!=contrat.dossier_id.numaff:
                    first=True
                    total = 0
                    mem = contrat.dossier_id.numaff
                    if color==color1:
                        color=color2
                    else:
                        color=color1

                cell = ws.cell(row=row, column=1, value=contrat.dossier_id.numaff)
                cell.alignment = Alignment(horizontal='center')
                cell.font = Font(name='Calibri', bold=False)
                cell.border = thin_border
                cell.fill = color

                cell = ws.cell(row=row, column=2, value=contrat.name)
                cell.alignment = Alignment(horizontal='center')
                cell.font = Font(name='Calibri', bold=False)
                cell.border = thin_border
                cell.fill = color

                cell = ws.cell(row=row, column=3, value=contrat.dossier_id.nom)
                cell.alignment = Alignment(horizontal='left')
                cell.font = Font(name='Calibri', bold=False)
                cell.border = thin_border
                cell.fill = color

                cell = ws.cell(row=row, column=4, value=line["code"])
                cell.alignment = Alignment(horizontal='center')
                cell.font = Font(name='Calibri', bold=False)
                cell.border = thin_border
                cell.fill = color

                cell = ws.cell(row=row, column=5, value=line["montant"])
                cell.alignment = Alignment(horizontal='right')
                cell.font = Font(name='Calibri', bold=False)
                cell.border = thin_border
                cell.fill = color
                cell.number_format = '# ##0.00'  # Number formatting


                if first:
                    value = totaux[contrat.dossier_id.numaff]
                    cell = ws.cell(row=row, column=6, value=value)
                    cell.alignment = Alignment(horizontal='right')
                    cell.font = Font(name='Calibri', bold=False)
                    cell.border = thin_border
                    cell.fill = color
                    cell.number_format = '# ##0.00'  # Number formatting

                first=False
                row+=1
            #******************************************************************

            #** Récapitulatif *************************************************
            row+=2
            titres=["Code MAF", "Montant HT"]
            column = 4
            for titre in titres:
                clr_background = PatternFill(start_color='FFFACD', end_color='FFFACD', fill_type="solid")
                cell = ws.cell(row=row, column=column, value=titre)
                cell.fill = clr_background
                cell.alignment = Alignment(horizontal='center')
                cell.font = Font(name='Calibri', bold=True)
                cell.border = thin_border
                column+=1
            row+=1
            recap2 = res[1]
            cell_start = cell_end = False
            for line in recap2:
                cell = ws.cell(row=row, column=4, value=line[0])
                cell.alignment = Alignment(horizontal='left')
                cell.font = Font(name='Calibri', bold=False)
                cell.border = thin_border

                cell = ws.cell(row=row, column=5, value=line[1])
                cell.alignment = Alignment(horizontal='right')
                cell.font = Font(name='Calibri', bold=False)
                cell.border = thin_border
                cell.number_format = '# ##0.00'  # Number formatting
                #** cell de début et de fin pour faire la somme ***************
                if cell_start==False:
                    cell_start = cell
                cell_end = cell
                row+=1
            #******************************************************************

            #** Total du récapitulatif ****************************************
            cell = ws.cell(row=row, column=4, value="Total : ")
            cell.alignment = Alignment(horizontal='left')
            cell.font = Font(name='Calibri', bold=True)
            cell.border = thin_border

            formula = "=SUM(%s:%s)"%(cell_start.coordinate, cell_end.coordinate)
            cell = ws.cell(row=row, column=5, value=formula)
            cell.alignment = Alignment(horizontal='right')
            cell.font = Font(name='Calibri', bold=True)
            cell.border = thin_border
            cell.number_format = '# ##0.00'  # Number formatting
            #******************************************************************

            #** Mise en page **************************************************
            ws.sheet_properties.pageSetUpPr.fitToPage = True
            ws.page_setup.fitToHeight = False
            ws.oddFooter.center.text = "Page &[Page] of &N"
            ws.page_margins = PageMargins(left=0.3, right=0.3, top=0.3, bottom=0.7, header=0, footer=0.3)
            ws.print_title_rows = '1:1' # the first two rows 
            ws.print_options.horizontalCentered = True
            #******************************************************************

            #** Fixer les lignes et les colonnes ******************************
            cel = ws['A2']
            ws.freeze_panes = cel
            #******************************************************************

            # #** Enregistrement du workbook ************************************
            workbook.save(path)
            # #******************************************************************

            # ** Creation ou modification de la pièce jointe ******************
            user  = self.env['res.users'].browse(self.env.uid)
            attachment_obj = self.env['ir.attachment']
            attachments = attachment_obj.search([('res_id','=',user.id),('name','=',name)])
            xlsx = open(path,'rb').read()
            vals = {
                'name':        name,
                'type':        'binary',
                'res_id':      user.id,
                'raw':         xlsx,
            }
            attachment_id=False
            if attachments:
                for attachment in attachments:
                    attachment.write(vals)
                    attachment_id=attachment.id
            else:
                attachment = attachment_obj.create(vals)
                attachment_id=attachment.id
            #*******************************************************************

            ##** Envoi de l'action dans le navigateur **************************
            if attachment_id:
                # Utiliser l'URL avec le nom du fichier dans le chemin
                # Cette méthode est plus robuste car le nom fait partie du chemin
                try:
                    from urllib.parse import quote  # Python 3
                except ImportError:
                    from urllib import quote  # Python 2
                filename_encoded = quote(name.encode('utf-8'))
                vals={
                    "type": 'ir.actions.act_url',
                    "url" : '/web/content/%s/%s?download=true'%(attachment_id, filename_encoded),
                    "target": "self",
                }
                return vals







class IsConcours(models.Model):
    _name = 'is.concours'
    _description = "Concours"
    _order = 'numconcours desc'
    _rec_name = 'numconcours'

    def _get_numconcours(self):
        prefix = _get_prefix_annee()+'CO'
        rows=self.env['is.concours'].search([('numconcours','like',prefix)],order="numconcours desc",limit=1)
        numconcours=1
        for row in rows:
            numconcours = int(row.numconcours[-3:])
            numconcours+=1
        numconcours=prefix+('000'+str(numconcours))[-3:]
        return numconcours

    numconcours    = fields.Char("Numero de concours", required=True, index=True, default=lambda self: self._get_numconcours())
    organisme_id   = fields.Many2one('res.partner', "Organisme", domain=[('is_company','=',True)])
    nom            = fields.Char("Nom du concours")
    libelle_exacte = fields.Text("Libelle exacte")
    lieu           = fields.Char("Lieu")
    dateparution   = fields.Date("Date de parution")
    daterendu      = fields.Date("Date rendu")
    journal        = fields.Char("Journal")
    lienannonce    = fields.Char("Lien annonce")
    qui_ids        = fields.One2many('is.concours.qui', 'concours_id', 'Equipes')


class IsConcoursQui(models.Model):
    _name = 'is.concours.qui'
    _description = "Concours Qui"
    _order = 'nom'
    _rec_name = 'nom'

    concours_id    = fields.Many2one('is.concours', 'Concours', required=True, ondelete='cascade')
    nom            = fields.Char("Nom", required=True, index=True)
    dateenvoi      = fields.Date("Date d'envoi")
    retenu         = fields.Selection([('oui','Oui'),('non','Non')],"Gagné" , default='non')
    gagne          = fields.Selection([('oui','Oui'),('non','Non')],"Retenu", default='non')
    equipes        = fields.Text("Equipes")
    idconcours_qui = fields.Integer("idconcours_qui", index=True)


    


