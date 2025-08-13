/**
 * Script principal du tableau de bord DEM
 * Gère les interactions et les appels API
 */

// Configuration de base
const API_BASE_URL = '/api';

// Fonction utilitaire pour formater les nombres
function formatNumber(num) {
    return new Intl.NumberFormat('fr-FR').format(num);
}

// Fonction utilitaire pour formater les dates
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('fr-FR', options);
}

// Fonction pour construire les paramètres de requête à partir des filtres
function buildQueryParams(filters = {}) {
    const params = new URLSearchParams();
    
    // Ajouter les filtres aux paramètres
    Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== '' && value !== undefined) {
            if (Array.isArray(value)) {
                value.forEach(v => params.append(key, v));
            } else {
                params.append(key, value);
            }
        }
    });
    
    return params.toString();
}

// Fonction pour appliquer les filtres
async function applyFilters() {
    const filters = {
        status: document.getElementById('filter-status').value || null,
        location: document.getElementById('filter-location').value || null,
        model: document.getElementById('filter-model').value || null,
        date_from: document.getElementById('filter-date-from').value || null,
        date_to: document.getElementById('filter-date-to').value || null,
    };
    
    // Mettre à jour l'URL avec les filtres actuels
    const queryString = buildQueryParams(filters);
    window.history.pushState({}, '', `?${queryString}`);
    
    // Recharger les données avec les filtres
    await loadKPIs(filters);
    await loadEquipmentsTable(filters);
    
    // Mettre à jour les graphiques
    updateCharts(filters);
}

// Fonction pour réinitialiser les filtres
function resetFilters() {
    document.getElementById('filter-status').value = '';
    document.getElementById('filter-location').value = '';
    document.getElementById('filter-model').value = '';
    document.getElementById('filter-date-from').value = '';
    document.getElementById('filter-date-to').value = '';
    
    // Appliquer la réinitialisation
    applyFilters();
}

// Fonction pour charger les KPI avec filtres
async function loadKPIs(filters = {}) {
    try {
        const queryString = buildQueryParams(filters);
        const response = await fetch(`${API_BASE_URL}/equipments/?${queryString}`);
        const data = await response.json();
        
        // Mettre à jour les compteurs
        document.getElementById('total-equipments').textContent = formatNumber(data.total);
        
        // Calculer la répartition par statut
        const statusCount = {};
        data.results.forEach(equipment => {
            const status = equipment.status || 'Inconnu';
            statusCount[status] = (statusCount[status] || 0) + 1;
        });
        
        // Mettre à jour les compteurs de statut
        for (const [status, count] of Object.entries(statusCount)) {
            const element = document.getElementById(`status-${status.toLowerCase().replace(/\\s+/g, '-')}`);
            if (element) {
                element.textContent = formatNumber(count);
            }
        }
        
        // Calculer la valeur totale du stock
        const totalValue = data.results.reduce((sum, equipment) => {
            return sum + (parseFloat(equipment.price) || 0);
        }, 0);
        
        document.getElementById('total-value').textContent = formatNumber(totalValue.toFixed(2)) + ' MAD';
        
    } catch (error) {
        console.error('Erreur lors du chargement des KPI:', error);
        showError('Erreur lors du chargement des données');
    }
}

// Fonction pour initialiser les graphiques
function initCharts() {
    // Graphique de répartition par statut
    const statusCtx = document.getElementById('statusChart').getContext('2d');
    
    // Configuration du graphique de répartition par statut
    const statusChart = new Chart(statusCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#4e73df', // Bleu pour En service
                    '#1cc88a', // Vert pour En stock
                    '#f6c23e', // Jaune pour En instance
                    '#e74a3b', // Rouge pour En panne
                    '#6f42c1', // Violet pour Hors service
                    '#858796'  // Gris pour Inconnu
                ],
                hoverBackgroundColor: [
                    '#2e59d9',
                    '#17a673',
                    '#dda20a',
                    '#be2617',
                    '#5a32a3',
                    '#6c757d'
                ],
                borderWidth: 1
            }]
        },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                title: {
                    display: true,
                    text: 'Répartition par statut',
                    font: {
                        size: 14,
                        weight: 'bold'
                    },
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '70%',
            animation: {
                animateScale: true,
                animateRotate: true
            }
        }
    });
    
    // Graphique d'évolution temporelle
    const timelineCtx = document.getElementById('timelineChart').getContext('2d');
    
    // Configuration du graphique d'évolution temporelle
    const timelineChart = new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Nouveaux équipements',
                    data: [],
                    borderColor: '#4e73df',
                    backgroundColor: 'rgba(78, 115, 223, 0.05)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointBackgroundColor: '#4e73df',
                    pointBorderColor: '#fff',
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: '#4e73df',
                    pointHoverBorderColor: '#fff',
                    pointHitRadius: 10,
                    pointBorderWidth: 2,
                    pointStyle: 'circle'
                }
            ]
        },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Évolution des équipements par mois',
                    font: {
                        size: 14,
                        weight: 'bold'
                    },
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        title: function(tooltipItems) {
                            return tooltipItems[0].label;
                        },
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw} équipement(s)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });
    
    // Stocker les instances de graphiques dans l'objet window pour pouvoir les mettre à jour plus tard
    window.statusChart = statusChart;
    window.timelineChart = timelineChart;
    
    console.log('Graphiques initialisés avec succès');
}

// Fonction pour afficher un message d'erreur
function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Ajouter l'alerte au début du contenu principal
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.insertBefore(alertDiv, mainContent.firstChild);
    }
    
    // Supprimer automatiquement après 5 secondes
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Fonction pour formater le texte (première lettre en majuscule, le reste en minuscules)
function formatText(text) {
    if (!text) return '';
    return text.toLowerCase()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Fonction pour mettre à jour les options des filtres
async function updateFilterOptions() {
    try {
        // Récupérer les statuts uniques
        const statusResponse = await fetch(`${API_BASE_URL}/equipments/statuses/`);
        if (statusResponse.ok) {
            const statuses = await statusResponse.json();
            const statusSelect = document.getElementById('statusFilter');
            
            // Vider les options existantes sauf la première
            while (statusSelect.options.length > 1) {
                statusSelect.remove(1);
            }
            
            // Normaliser et dédupliquer les statuts
            const uniqueStatuses = [];
            const seenStatuses = new Set();
            
            statuses.forEach(status => {
                if (status) {
                    const normalized = normalizeStatus(status);
                    if (!seenStatuses.has(normalized)) {
                        seenStatuses.add(normalized);
                        uniqueStatuses.push(normalized);
                    }
                }
            });
            
            // Trier les statuts par ordre logique
            const statusOrder = [
                'EN SERVICE', 
                'EN STOCK', 
                'EN INSTANCE', 
                'EN PANNE', 
                'HORS SERVICE'
            ];
            
            const sortedStatuses = uniqueStatuses.sort((a, b) => {
                const indexA = statusOrder.indexOf(a);
                const indexB = statusOrder.indexOf(b);
                
                // Si les deux statuts sont dans l'ordre défini, les trier selon cet ordre
                if (indexA !== -1 && indexB !== -1) {
                    return indexA - indexB;
                }
                // Si seul a est dans l'ordre défini, le placer avant
                if (indexA !== -1) return -1;
                // Si seul b est dans l'ordre défini, le placer avant
                if (indexB !== -1) return 1;
                // Sinon, trier alphabétiquement
                return a.localeCompare(b);
            });
            
            // Ajouter les options triées
            sortedStatuses.forEach(status => {
                const option = document.createElement('option');
                option.value = status;
                option.textContent = formatText(status);
                statusSelect.appendChild(option);
            });
        }
        
        // Récupérer les localisations uniques
        const locationResponse = await fetch(`${API_BASE_URL}/equipments/locations/`);
        if (locationResponse.ok) {
            const locations = await locationResponse.json();
            const locationSelect = document.getElementById('locationFilter');
            
            // Vider les options existantes sauf la première
            while (locationSelect.options.length > 1) {
                locationSelect.remove(1);
            }
            
            // Trier les localisations par ordre alphabétique
            const sortedLocations = [...new Set(locations)]
                .filter(loc => loc) // Filtrer les valeurs nulles/vides
                .sort((a, b) => a.localeCompare(b, 'fr', {sensitivity: 'base'}));
            
            // Ajouter les options triées
            sortedLocations.forEach(location => {
                const option = document.createElement('option');
                option.value = location;
                option.textContent = formatText(location);
                locationSelect.appendChild(option);
            });
        }
        
        console.log('Options de filtre mises à jour avec succès');
    } catch (error) {
        console.error('Erreur lors de la mise à jour des options de filtre:', error);
        showError('Erreur lors du chargement des options de filtre');
    }
}

// Fonction pour charger les options des filtres
async function loadFilterOptions() {
    try {
        // Charger les statuts uniques
        const statusResponse = await fetch(`${API_BASE_URL}/equipments/?group_by=status`);
        const statusData = await statusResponse.json();
        const statusSelect = document.getElementById('filter-status');
        
        if (statusSelect) {
            statusData.forEach(status => {
                if (status) {
                    const option = document.createElement('option');
                    option.value = status;
                    option.textContent = status;
                    statusSelect.appendChild(option);
                }
            });
        }
        
        // Charger les localisations uniques
        const locationResponse = await fetch(`${API_BASE_URL}/equipments/?group_by=location`);
        const locationData = await locationResponse.json();
        const locationSelect = document.getElementById('filter-location');
        
        if (locationSelect) {
            locationData.forEach(location => {
                if (location) {
                    const option = document.createElement('option');
                    option.value = location;
                    option.textContent = location;
                    locationSelect.appendChild(option);
                }
            });
        }
        
    } catch (error) {
        console.error('Erreur lors du chargement des options de filtre:', error);
        showError('Erreur lors du chargement des options de filtre');
    }
}

// Fonction pour charger le tableau des équipements avec filtres
async function loadEquipmentsTable(filters = {}) {
    try {
        const queryString = buildQueryParams(filters);
        const response = await fetch(`${API_BASE_URL}/equipments/?${queryString}`);
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        const tbody = document.querySelector('#equipmentsTable tbody');
        
        if (!tbody) return;
        
        // Afficher le message de chargement
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Chargement...</span>
                    </div>
                </td>
            </tr>`;
        
        // Vider le tableau
        tbody.innerHTML = '';
        
        // Vérifier si des résultats sont disponibles
        if (!data.results || data.results.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center">
                        Aucun équipement trouvé avec les critères sélectionnés.
                    </td>
                </tr>`;
            return;
        }
        
        // Ajouter les lignes du tableau
        data.results.forEach(equipment => {
            const row = document.createElement('tr');
            
            // Définir une classe de badge Bootstrap en fonction du statut
            let statusClass = 'bg-secondary'; // Classe par défaut
            switch(equipment.status) {
                case 'En stock':
                    statusClass = 'bg-primary';
                    break;
                case 'En service':
                    statusClass = 'bg-success';
                    break;
                case 'Maintenance':
                    statusClass = 'bg-warning';
                    break;
                case 'Hors service':
                    statusClass = 'bg-danger';
                    break;
                default:
                    statusClass = 'bg-secondary';
            }
            
            row.innerHTML = `
                <td>${equipment.model || 'N/A'}</td>
                <td>${equipment.serial || 'N/A'}</td>
                <td>${equipment.barcode || 'N/A'}</td>
                <td><span class="badge ${statusClass}">${equipment.status || 'Inconnu'}</span></td>
                <td>${equipment.location || 'N/A'}</td>
                <td>${formatDate(equipment.creation_date)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="viewEquipment('${equipment._id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="editEquipment('${equipment._id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            `;
            
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Erreur lors du chargement du tableau des équipements:', error);
    }
}

// Fonctions pour les boutons d'action
function viewEquipment(id) {
    console.log('Voir équipement:', id);
    // Implémenter la logique pour afficher les détails de l'équipement
}

function editEquipment(id) {
    console.log('Modifier équipement:', id);
    // Implémenter la logique pour modifier l'équipement
}

// Fonction pour normaliser les statuts (regroupement des variantes)
function normalizeStatus(status) {
    if (!status) return 'INCONNU';
    
    const statusMap = {
        // En service
        'EN SERVICE': 'EN SERVICE',
        'En Service': 'EN SERVICE',
        'En service': 'EN SERVICE',
        'en service': 'EN SERVICE',
        'EN Service': 'EN SERVICE',
        
        // En stock
        'EN STOCK': 'EN STOCK',
        'En Stock': 'EN STOCK',
        'En stock': 'EN STOCK',
        'en stock': 'EN STOCK',
        
        // En panne
        'EN PANNE': 'EN PANNE',
        'En panne': 'EN PANNE',
        'en panne': 'EN PANNE',
        'EN panne': 'EN PANNE',
        
        // Hors service
        'HS': 'HORS SERVICE',
        'hs': 'HORS SERVICE',
        'Hors service': 'HORS SERVICE',
        'HORS SERVICE': 'HORS SERVICE',
        
        // En instance
        'En instance': 'EN INSTANCE',
        'EN INSTANCE': 'EN INSTANCE'
    };
    
    // Nettoyer les espaces en trop et convertir en majuscules
    const cleanStatus = status.toString().trim().toUpperCase();
    
    // Retourner la version normalisée ou la valeur d'origine si non trouvée
    return statusMap[cleanStatus] || cleanStatus;
}

// Fonction pour grouper les données par mois
function groupDataByMonth(data) {
    const monthlyData = {};
    
    data.forEach(item => {
        if (!item || !item._id) return;
        
        try {
            const date = new Date(item._id);
            // Créer une clé au format 'YYYY-MM' pour le regroupement par mois
            const monthKey = date.toISOString().substring(0, 7);
            
            if (!monthlyData[monthKey]) {
                monthlyData[monthKey] = 0;
            }
            
            monthlyData[monthKey] += item.count || 0;
        } catch (e) {
            console.error('Erreur de traitement de la date:', item._id, e);
        }
    });
    
    // Convertir l'objet en tableau trié
    return Object.entries(monthlyData)
        .map(([month, count]) => ({
            month,
            count,
            label: new Date(month).toLocaleDateString('fr-FR', { month: 'short', year: '2-digit' })
        }))
        .sort((a, b) => a.month.localeCompare(b.month));
}

// Fonction pour mettre à jour les graphiques avec les filtres
async function updateCharts(filters = {}) {
    const queryString = buildQueryParams(filters);
    
    try {
        console.log('Mise à jour des graphiques avec les filtres:', filters);
        
        // 1. Mettre à jour le graphique de répartition par statut
        try {
            console.log('Récupération des données de statut...');
            const statusResponse = await fetch(`${API_BASE_URL}/equipments/?group_by=status&${queryString}`);
            if (!statusResponse.ok) {
                throw new Error(`Erreur HTTP: ${statusResponse.status}`);
            }
            const statusData = await statusResponse.json();
            console.log('Données de statut reçues:', statusData);
            
            if (window.statusChart) {
                // Normaliser et regrouper les statuts
                const normalizedStatuses = {};
                
                statusData.forEach(item => {
                    if (item && item._id) {
                        const normalized = normalizeStatus(item._id);
                        normalizedStatuses[normalized] = (normalizedStatuses[normalized] || 0) + (item.count || 0);
                    }
                });
                
                // Convertir en tableaux pour le graphique
                const labels = Object.keys(normalizedStatuses);
                const counts = Object.values(normalizedStatuses);
                
                // Vérifier qu'on a des données
                if (labels.length > 0 && counts.length > 0) {
                    window.statusChart.data.labels = labels;
                    window.statusChart.data.datasets[0].data = counts;
                    window.statusChart.update();
                    console.log('Graphique de statut mis à jour avec succès');
                } else {
                    console.warn('Aucune donnée de statut valide pour mettre à jour le graphique');
                }
            } else {
                console.warn('Le graphique de statut n\'est pas initialisé');
            }
        } catch (statusError) {
            console.error('Erreur lors de la mise à jour du graphique de statut:', statusError);
            showError('Erreur lors du chargement des statistiques par statut');
        }
        
        // 2. Mettre à jour le graphique d'évolution temporelle
        try {
            console.log('Récupération des données d\'évolution temporelle...');
            const timelineResponse = await fetch(`${API_BASE_URL}/equipments/?group_by=creation_date&${queryString}`);
            if (!timelineResponse.ok) {
                throw new Error(`Erreur HTTP: ${timelineResponse.status}`);
            }
            const timelineData = await timelineResponse.json();
            console.log('Données d\'évolution temporelle reçues:', timelineData);
            
            if (window.timelineChart) {
                // Vérifier si nous avons des données
                if (!Array.isArray(timelineData) || timelineData.length === 0) {
                    console.warn('Aucune donnée d\'évolution temporelle disponible');
                    return;
                }
                
                // Grouper les données par mois
                const monthlyData = groupDataByMonth(timelineData);
                
                if (monthlyData.length > 0) {
                    const labels = monthlyData.map(item => item.label);
                    const counts = monthlyData.map(item => item.count);
                    
                    window.timelineChart.data.labels = labels;
                    window.timelineChart.data.datasets[0].data = counts;
                    window.timelineChart.update();
                    console.log('Graphique d\'évolution temporelle mis à jour avec succès');
                } else {
                    console.warn('Aucune donnée valide pour le graphique d\'évolution temporelle après regroupement par mois');
                }
            } else {
                console.warn('Le graphique d\'évolution temporelle n\'est pas initialisé');
            }
        } catch (timelineError) {
            console.error('Erreur lors de la mise à jour du graphique d\'évolution temporelle:', timelineError);
            // Ne pas afficher d'erreur à l'utilisateur pour éviter les messages redondants
        }
        
    } catch (error) {
        console.error('Erreur critique lors de la mise à jour des graphiques:', error);
        showError('Erreur lors de la mise à jour des graphiques');
    }
}

// Initialisation de la page
document.addEventListener('DOMContentLoaded', function() {
    // Charger les options des filtres
    loadFilterOptions();
    
    // Récupérer les filtres depuis l'URL
    const urlParams = new URLSearchParams(window.location.search);
    const filters = {
        status: urlParams.get('status') || '',
        location: urlParams.get('location') || '',
        model: urlParams.get('model') || '',
        date_from: urlParams.get('date_from') || '',
        date_to: urlParams.get('date_to') || ''
    };
    
    // Appliquer les filtres depuis l'URL
    Object.entries(filters).forEach(([key, value]) => {
        const element = document.getElementById(`filter-${key}`);
        if (element && value) {
            element.value = value;
        }
    });
    
    // Initialiser les graphiques
    initCharts();
    
    // Charger les données avec les filtres initiaux
    loadKPIs(filters).then(() => {
        loadEquipmentsTable(filters);
        updateCharts(filters);
    });
    
    // Gestionnaire d'événements pour les filtres
    const filterInputs = document.querySelectorAll('.filter-input');
    filterInputs.forEach(input => {
        input.addEventListener('change', applyFilters);
    });
    
    // Gestionnaire pour le bouton de réinitialisation
    const resetButton = document.getElementById('reset-filters');
    if (resetButton) {
        resetButton.addEventListener('click', resetFilters);
    }
    
    // Gestionnaire pour la recherche en temps réel
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                applyFilters();
            }, 500);
        });
    }
    
    // Gestionnaire pour le bouton de basculement du menu latéral
    const sidebarToggle = document.querySelector('[data-bs-target="#sidebar"]');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.getElementById('sidebar').classList.toggle('show');
        });
    }
    
    // Fermer le menu latéral lors du clic en dehors sur mobile
    document.addEventListener('click', function(event) {
        const sidebar = document.getElementById('sidebar');
        const isClickInsideSidebar = sidebar.contains(event.target);
        const isClickOnToggleButton = sidebarToggle && (sidebarToggle === event.target || sidebarToggle.contains(event.target));
        
        if (window.innerWidth <= 768 && !isClickInsideSidebar && !isClickOnToggleButton) {
            sidebar.classList.remove('show');
        }
    });
    
    // Gérer le redimensionnement de la fenêtre
    window.addEventListener('resize', function() {
        const sidebar = document.getElementById('sidebar');
        if (window.innerWidth > 768) {
            sidebar.classList.remove('show');
        }
    });
});
