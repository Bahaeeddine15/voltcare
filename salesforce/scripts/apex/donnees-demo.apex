// =====================================================================
// VoltCare — Données de démonstration (VC-69 / US-04)
// Lancer : sf apex run --file scripts/apex/donnees-demo.apex --target-org <alias>
// Idempotent : upsert sur les External IDs (Code_Station__c, Code_Borne__c,
// Badge_RFID__c). Relancer le script remet les données dans leur état initial
// (utile pour réinitialiser l'org avant la soutenance).
// Le technicien des stations = l'utilisateur qui lance le script.
// =====================================================================

Id technicienId = UserInfo.getUserId();

// ---------- 1. Compte « Clients VoltCare » (pas d'External ID : recherche par nom)
List<Account> comptes = [SELECT Id FROM Account WHERE Name = 'Clients VoltCare' LIMIT 1];
Account compteClients = comptes.isEmpty() ? new Account(Name = 'Clients VoltCare') : comptes[0];
upsert compteClients;

// ---------- 2. 3 clients avec badge
List<Contact> clients = new List<Contact>{
    new Contact(FirstName = 'Yassine', LastName = 'El Amrani', Email = 'yassine.elamrani@example.com', Badge_RFID__c = 'CLI-0001', AccountId = compteClients.Id),
    new Contact(FirstName = 'Salma',   LastName = 'Bennani',   Email = 'salma.bennani@example.com',    Badge_RFID__c = 'CLI-0002', AccountId = compteClients.Id),
    new Contact(FirstName = 'Omar',    LastName = 'Tazi',      Email = 'omar.tazi@example.com',        Badge_RFID__c = 'CLI-0003', AccountId = compteClients.Id)
};
upsert clients Contact.Badge_RFID__c;

// ---------- 3. 6 stations (2 par ville), localisation GPS réelle
List<Station__c> stations = new List<Station__c>{
    new Station__c(Code_Station__c = 'ST-MRK-01', Name = 'Marrakech Guéliz',         Ville__c = 'Marrakech',  Adresse__c = 'Avenue Mohammed V, Guéliz',           Localisation__Latitude__s = 31.6365, Localisation__Longitude__s = -8.0103, Technicien__c = technicienId),
    new Station__c(Code_Station__c = 'ST-MRK-02', Name = 'Marrakech Menara Mall',    Ville__c = 'Marrakech',  Adresse__c = 'Avenue Mohammed VI, Menara Mall',     Localisation__Latitude__s = 31.6142, Localisation__Longitude__s = -8.0285, Technicien__c = technicienId),
    new Station__c(Code_Station__c = 'ST-CAS-01', Name = 'Casablanca Morocco Mall',  Ville__c = 'Casablanca', Adresse__c = 'Boulevard de la Corniche, Aïn Diab',  Localisation__Latitude__s = 33.5760, Localisation__Longitude__s = -7.7066, Technicien__c = technicienId),
    new Station__c(Code_Station__c = 'ST-CAS-02', Name = 'Casablanca Anfaplace',     Ville__c = 'Casablanca', Adresse__c = 'Boulevard de la Corniche, Anfa',      Localisation__Latitude__s = 33.6000, Localisation__Longitude__s = -7.6600, Technicien__c = technicienId),
    new Station__c(Code_Station__c = 'ST-RBT-01', Name = 'Rabat Agdal',              Ville__c = 'Rabat',      Adresse__c = 'Avenue de France, Agdal',             Localisation__Latitude__s = 33.9967, Localisation__Longitude__s = -6.8498, Technicien__c = technicienId),
    new Station__c(Code_Station__c = 'ST-RBT-02', Name = 'Rabat Hay Riad',           Ville__c = 'Rabat',      Adresse__c = 'Avenue Annakhil, Hay Riad',           Localisation__Latitude__s = 33.9592, Localisation__Longitude__s = -6.8710, Technicien__c = technicienId)
};
upsert stations Station__c.Code_Station__c;

// ---------- 4. 15 bornes : 3 sur la station 01, 2 sur la station 02 de chaque ville
List<String> villes = new List<String>{ 'MRK', 'CAS', 'RBT' };
List<String> fabricants = new List<String>{ 'ABB', 'Schneider Electric', 'Wallbox', 'ABB', 'Schneider Electric' };
List<String> modeles    = new List<String>{ 'Terra AC W22', 'EVlink Pro AC', 'Commander 2', 'Terra AC W22', 'EVlink Pro AC' };
List<Decimal> puissances = new List<Decimal>{ 22, 22, 11, 22, 22 };

List<Borne__c> bornes = new List<Borne__c>();
for (String ville : villes) {
    for (Integer i = 1; i <= 5; i++) {
        String code = ville + '-' + String.valueOf(i).leftPad(3, '0');          // MRK-001
        String codeStation = 'ST-' + ville + (i <= 3 ? '-01' : '-02');           // ST-MRK-01 / 02
        bornes.add(new Borne__c(
            Code_Borne__c = code,
            Name = code,
            Station__r = new Station__c(Code_Station__c = codeStation),
            Statut__c = 'Disponible',
            Joignable__c = true,
            Fabricant__c = fabricants[i - 1],
            Modele__c = modeles[i - 1],
            Puissance_Max_kW__c = puissances[i - 1],
            Date_Mise_En_Service__c = Date.today().addMonths(-(6 + i * 4))      // 10 à 26 mois d'ancienneté
        ));
    }
}
upsert bornes Borne__c.Code_Borne__c;

System.debug('VoltCare démo : ' + clients.size() + ' clients, ' + stations.size() + ' stations, ' + bornes.size() + ' bornes.');
