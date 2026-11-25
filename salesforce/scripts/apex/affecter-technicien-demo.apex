// VoltCare — VC-70 : rattache les 6 stations de démo au technicien de démo.
// Lancer APRÈS donnees-demo.apex (qui met l'admin comme technicien) :
//   sf apex run --file scripts/apex/affecter-technicien-demo.apex --target-org voltcare-demo
// Le technicien de démo = l'utilisateur actif dont le rôle est « Technicien ».

List<User> techniciens = [SELECT Id, Name FROM User WHERE IsActive = true AND UserRole.DeveloperName = 'Technicien' ORDER BY CreatedDate LIMIT 1];
if (techniciens.isEmpty()) {
    System.debug('Aucun utilisateur actif avec le rôle Technicien : créer le technicien de démo d\'abord.');
} else {
    List<Station__c> stations = [SELECT Id FROM Station__c WHERE Code_Station__c LIKE 'ST-___-0_'];
    for (Station__c s : stations) {
        s.Technicien__c = techniciens[0].Id;
    }
    update stations;
    System.debug(stations.size() + ' stations rattachées à ' + techniciens[0].Name);
}
