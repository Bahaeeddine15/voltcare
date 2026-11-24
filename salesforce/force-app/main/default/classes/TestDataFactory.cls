/**
 * Fabrique de données de test VoltCare, réutilisée par toutes les classes de test.
 * Références : strategie-tests.md §3.3, dictionnaire-donnees.md v1.3, securite.md v1.1
 */
@IsTest
public class TestDataFactory {

    public class TestDataException extends Exception {}

    public static final String NOM_COMPTE_CLIENTS = 'Clients VoltCare';

    public static final String PS_RESPONSABLE = 'VoltCare_Responsable';
    public static final String PS_TECHNICIEN  = 'VoltCare_Technicien';
    public static final String PS_PASSERELLE  = 'VoltCare_Passerelle';

    private static final List<String> PROFILS_INTERNES = new List<String>{
        'VoltCare Interne', 'Minimum Access - Salesforce', 'Standard User'
    };
    private static final List<String> PROFILS_PASSERELLE = new List<String>{
        'Minimum Access - API Only Integrations'
    };

    // Rôles créés une seule fois par transaction : Responsable > Technicien
    private static Id roleResponsableId;
    private static Id roleTechnicienId;

    // ------------------------------------------------------------------
    // Clients
    // ------------------------------------------------------------------

    /** Retourne le compte « Clients VoltCare » (le crée s'il n'existe pas). */
    public static Account creerCompteClients() {
        List<Account> existants = [SELECT Id FROM Account WHERE Name = :NOM_COMPTE_CLIENTS LIMIT 1];
        if (!existants.isEmpty()) {
            return existants[0];
        }
        Account compte = new Account(Name = NOM_COMPTE_CLIENTS);
        insert compte;
        return compte;
    }

    /** Client = Contact rattaché au compte « Clients VoltCare », avec son badge RFID. */
    public static Contact creerClient(String nom, String badgeRfid) {
        Contact client = new Contact(
            LastName = nom,
            Badge_RFID__c = badgeRfid,
            AccountId = creerCompteClients().Id
        );
        insert client;
        return client;
    }

    // ------------------------------------------------------------------
    // Stations, bornes, sessions, tickets
    // ------------------------------------------------------------------

    public static Station__c creerStation(String code, String ville, Id technicienId) {
        Station__c station = new Station__c(
            Name = 'Station ' + code,
            Code_Station__c = code,
            Ville__c = ville,
            Adresse__c = '1 rue du Test',
            Localisation__Latitude__s = 31.6295,
            Localisation__Longitude__s = -7.9811,
            Technicien__c = technicienId
        );
        insert station;
        return station;
    }

    public static Borne__c creerBorne(String code, Id stationId) {
        Borne__c borne = nouvelleBorne(code, stationId);
        insert borne;
        return borne;
    }

    /** Crée nb bornes : prefixe-001, prefixe-002, ... (ex. MRK-001). */
    public static List<Borne__c> creerBornes(Id stationId, String prefixe, Integer nb) {
        List<Borne__c> bornes = new List<Borne__c>();
        for (Integer i = 1; i <= nb; i++) {
            bornes.add(nouvelleBorne(prefixe + '-' + String.valueOf(i).leftPad(3, '0'), stationId));
        }
        insert bornes;
        return bornes;
    }

    private static Borne__c nouvelleBorne(String code, Id stationId) {
        return new Borne__c(
            Name = code,
            Code_Borne__c = code,
            Station__c = stationId,
            Statut__c = 'Disponible',
            Date_Mise_En_Service__c = Date.today().addMonths(-12)
        );
    }

   
    public static Session_Recharge__c creerSession(Borne__c borne, Contact client, Integer transactionId) {
        Session_Recharge__c session = new Session_Recharge__c(
            Borne__c = borne.Id,
            Client__c = (client == null) ? null : client.Id,
            Cle_Session__c = borne.Code_Borne__c + '-' + transactionId,
            Transaction_Id__c = transactionId,
            Id_Tag__c = (client == null) ? 'INCONNU' : client.Badge_RFID__c,
            Date_Debut__c = Datetime.now().addHours(-1),
            Compteur_Debut_Wh__c = 1000,
            Statut__c = 'En cours'
        );
        insert session;
        return session;
    }
   

    /**
     * Ticket explicitement affecté à proprietaireId.
     * (Le Flow d'affectation donnerait la même valeur : technicien de la station.)
     */
    public static Case creerTicket(Id borneId, Id proprietaireId, String type) {
        Case ticket = new Case(
            Subject = 'Ticket de test ' + type,
            Type = type,
            Origin = 'Borne',
            Status = 'Nouveau',
            Priority = 'Haute',
            Borne__c = borneId,
            OwnerId = proprietaireId
        );
        insert ticket;
        return ticket;
    }

    // ------------------------------------------------------------------
    // Utilisateurs (avec leurs Permission Sets)
    // ------------------------------------------------------------------

    public static User creerTechnicien(String alias) {
        return creerUtilisateur(alias, PROFILS_INTERNES, true, false, PS_TECHNICIEN);
    }

    public static User creerResponsable(String alias) {
        return creerUtilisateur(alias, PROFILS_INTERNES, true, true, PS_RESPONSABLE);
    }

    public static User creerPasserelle(String alias) {
        return creerUtilisateur(alias, PROFILS_PASSERELLE, false, false, PS_PASSERELLE);
    }

    /**
     * Les objets de configuration (User, rôle, Permission Set) et les objets métier
     * ne peuvent pas être modifiés dans la même transaction : on isole la configuration
     * dans un bloc runAs pour éviter l'erreur MIXED_DML_OPERATION.
     */
    private static User creerUtilisateur(
        String alias, List<String> profils, Boolean avecRole, Boolean estResponsable, String permissionSet
    ) {
        User utilisateur;
        System.runAs(new User(Id = UserInfo.getUserId())) {
            Id roleId = null;
            if (avecRole) {
                creerRolesSiNecessaire();
                roleId = estResponsable ? roleResponsableId : roleTechnicienId;
            }
            utilisateur = new User(
                Alias = alias,
                LastName = 'Test ' + alias,
                Email = alias + '@voltcare-test.example',
                Username = alias + '.' + System.currentTimeMillis() + '@voltcare-test.example',
                ProfileId = idProfil(profils),
                UserRoleId = roleId,
                EmailEncodingKey = 'UTF-8',
                LanguageLocaleKey = 'fr',
                LocaleSidKey = 'fr_FR',
                TimeZoneSidKey = 'Africa/Casablanca'
            );
            insert utilisateur;
            insert new PermissionSetAssignment(
                AssigneeId = utilisateur.Id,
                PermissionSetId = idPermissionSet(permissionSet)
            );
        }
        return utilisateur;
    }

    private static void creerRolesSiNecessaire() {
        if (roleResponsableId != null) {
            return;
        }
        UserRole responsable = new UserRole(
            Name = 'Test Responsable réseau',
            DeveloperName = 'Test_Responsable_Reseau'
        );
        insert responsable;
        UserRole technicien = new UserRole(
            Name = 'Test Technicien',
            DeveloperName = 'Test_Technicien',
            ParentRoleId = responsable.Id
        );
        insert technicien;
        roleResponsableId = responsable.Id;
        roleTechnicienId = technicien.Id;
    }

    /** Premier profil trouvé dans la liste (ordre de préférence). */
    private static Id idProfil(List<String> noms) {
        Map<String, Id> parNom = new Map<String, Id>();
        for (Profile p : [SELECT Id, Name FROM Profile WHERE Name IN :noms]) {
            parNom.put(p.Name, p.Id);
        }
        for (String nom : noms) {
            if (parNom.containsKey(nom)) {
                return parNom.get(nom);
            }
        }
        throw new TestDataException('Aucun profil trouvé parmi : ' + noms);
    }

    private static Id idPermissionSet(String nom) {
        List<PermissionSet> liste = [SELECT Id FROM PermissionSet WHERE Name = :nom LIMIT 1];
        if (liste.isEmpty()) {
            throw new TestDataException(
                'Permission Set introuvable : ' + nom + ' (déployé depuis salesforce/ ? voir VC-63 / VC-64)'
            );
        }
        return liste[0].Id;
    }
}
