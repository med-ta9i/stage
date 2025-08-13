// Fonction pour formater les nombres avec des espaces comme séparateurs de milliers
function formatNumber(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

// Fonction pour charger les indicateurs clés
function loadKeyMetrics() {
    fetch('/api/analytics/status-distribution/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateKeyMetrics(data.data);
            } else {
                console.error('Erreur lors du chargement des indicateurs clés:', data.error);
            }
        })
        .catch(error => console.error('Erreur:', error));
}

// Fonction pour mettre à jour les indicateurs clés
function updateKeyMetrics(data) {
    let totalEquipment = 0;
    let inService = 0;
    let inMaintenance = 0;
    let inStock = 0;
    let outOfService = 0;
    let totalValue = 0;

    // Parcourir les données pour calculer les totaux
    data.labels.forEach((status, index) => {
        const count = data.counts[index];
        const value = data.values[index] || 0;
        
        totalEquipment += count;
        totalValue += parseFloat(value) || 0;
        
        // Gestion des différents statuts avec correspondance insensible à la casse
        const statusLower = status.toLowerCase();
        
        if (statusLower.includes('service') && !statusLower.includes('hors')) {
            inService += count;
        } else if (statusLower.includes('stock') || statusLower.includes('instance')) {
            inStock += count;
            
            // Si 'instance' est considéré comme maintenance
            if (statusLower.includes('instance')) {
                inMaintenance += count;
            }
        } else if (statusLower.includes('hors') || statusLower.includes('panne') || statusLower === 'hs') {
            outOfService += count;
        } else if (statusLower.includes('maintenance')) {
            inMaintenance += count;
        }
    });

    // Mettre à jour l'interface utilisateur avec les totaux
    document.getElementById('total-equipment').textContent = formatNumber(totalEquipment);
    document.getElementById('in-service').textContent = formatNumber(inService);
    document.getElementById('in-maintenance').textContent = formatNumber(inMaintenance || outOfService); // Utiliser outOfService si inMaintenance est 0
    
    // Formater la valeur totale avec le symbole € et deux décimales
    const formattedValue = totalValue > 0 ? totalValue.toFixed(2) + ' €' : 'Non disponible';
    document.getElementById('total-value').textContent = formattedValue;
    
    // Mettre à jour les tooltips ou infobulles avec plus de détails
    document.getElementById('in-service').title = `${inService} équipements en service`;
    document.getElementById('in-maintenance').title = `${inMaintenance} équipements en maintenance / hors service`;
    document.getElementById('total-value').title = totalValue > 0 ? `Valeur totale estimée du parc` : 'Valeurs d\'achat non renseignées';
}

// Fonction pour afficher un message de débogage
function logDebug(message) {
    console.log('[Dashboard] ' + message);
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    logDebug('Script dashboard.js chargé avec succès');
    
    // Vérifier si les éléments du DOM existent
    if (!document.getElementById('total-equipment')) {
        logDebug('ERREUR: Élément #total-equipment non trouvé dans le DOM');
    } else {
        logDebug('Éléments du DOM trouvés, chargement des indicateurs...');
        // Charger les indicateurs clés
        loadKeyMetrics();
        
        // Actualiser les indicateurs toutes les 5 minutes
        setInterval(loadKeyMetrics, 5 * 60 * 1000);
    }
});
