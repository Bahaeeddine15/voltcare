/**
 * Vérifie le moindre privilège défini dans securite.md v1.1 :
 *  - un technicien ne voit que ses propres tickets (OWD Case privé)
 *  - l'utilisateur Passerelle n'a accès à aucun objet métier
 */
@IsTest
private class SecuriteTest {

    @TestSetup
    static void donnees() {
        User tech1 = TestDataFactory.creerTechnicien('tech1');
        User tech2 = TestDataFactory.creerTechnicien('tech2');
        TestDataFactory.creerPasserelle('gate');

        // Chaque technicien a sa station, donc ses tickets
        Station__c station1 = TestDataFactory.creerStation('ST-TST-01', 'Marrakech', tech1.Id);
        Station__c station2 = TestDataFactory.creerStation('ST-TST-02', 'Rabat', tech2.Id);
        Borne__c borne1 = TestDataFactory.creerBorne('MRK-901', station1.Id);
        Borne__c borne2 = TestDataFactory.creerBorne('RBT-901', station2.Id);

        TestDataFactory.creerTicket(borne1.Id, tech1.Id, 'Panne');
        TestDataFactory.creerTicket(borne2.Id, tech2.Id, 'Panne');
    }

    private static User utilisateur(String alias) {
        return [SELECT Id FROM User WHERE Alias = :alias LIMIT 1];
    }

    @IsTest
    static void technicienNeVoitQueSesTickets() {
        User tech1 = utilisateur('tech1');
        User tech2 = utilisateur('tech2');

        System.runAs(tech1) {
            List<Case> tickets = [SELECT Id, OwnerId FROM Case];
            Assert.areEqual(1, tickets.size(), 'Le technicien 1 ne doit voir qu\'un ticket');
            Assert.areEqual(tech1.Id, tickets[0].OwnerId, 'Le ticket visible doit appartenir au technicien 1');
        }

        System.runAs(tech2) {
            List<Case> tickets = [SELECT Id, OwnerId FROM Case];
            Assert.areEqual(1, tickets.size(), 'Le technicien 2 ne doit voir qu\'un ticket');
            Assert.areEqual(tech2.Id, tickets[0].OwnerId, 'Le ticket visible doit appartenir au technicien 2');
        }
    }

    @IsTest
    static void passerelleNePeutPasLireBorne() {
        User passerelle = utilisateur('gate');

        System.runAs(passerelle) {
            Assert.isFalse(Schema.sObjectType.Borne__c.isAccessible(), 'La passerelle ne doit pas avoir de droit de lecture sur Borne__c');

            Boolean refuse = false;
            try {
                Database.query('SELECT Id FROM Borne__c WITH USER_MODE');
            } catch (QueryException e) {
                refuse = true;
            }
            Assert.isTrue(refuse, 'La lecture de Borne__c doit être refusée à la passerelle');
        }
    }

    @IsTest
    static void passerelleNAccedeAAucunObjetMetier() {
        User passerelle = utilisateur('gate');

        System.runAs(passerelle) {
            Assert.isFalse(Schema.sObjectType.Station__c.isAccessible(), 'Station__c');
            Assert.isFalse(Schema.sObjectType.Session_Recharge__c.isAccessible(), 'Session_Recharge__c');
            Assert.isFalse(Schema.sObjectType.Mesure_Borne__c.isAccessible(), 'Mesure_Borne__c');
            Assert.isFalse(Schema.sObjectType.Case.isAccessible(), 'Case');
            Assert.isFalse(Schema.sObjectType.Integration_Log__c.isAccessible(), 'Integration_Log__c');
        }
    }

    @IsTest
    static void passerellePeutPublierDesEvenements() {
        User passerelle = utilisateur('gate');

        System.runAs(passerelle) {
            Assert.isTrue(Schema.sObjectType.Borne_Event__e.isCreateable(), 'La passerelle doit pouvoir créer des Borne_Event__e');
        }
    }
}

