let map;
let pickupAutocomplete;
let destinationAutocomplete;
let pickupLocation = null;
let destinationLocation = null;
let directionsRenderer;
let directionsService;
let watchPositionId = null;

// Initialize Google Maps
function initMap() {
    const center = { lat: 6.5244, lng: 3.3792 }; // Lagos coordinates
    
    map = new google.maps.Map(document.getElementById('map'), {
        center: center,
        zoom: 13
    });
    
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer();
    directionsRenderer.setMap(map);
    
    // Initialize autocomplete
    pickupAutocomplete = new google.maps.places.Autocomplete(
        document.getElementById('pickupInput')
    );
    destinationAutocomplete = new google.maps.places.Autocomplete(
        document.getElementById('destinationInput')
    );
    
    pickupAutocomplete.addListener('place_changed', onPickupChange);
    destinationAutocomplete.addListener('place_changed', onDestinationChange);
    
    // Get user location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const userLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };
            map.setCenter(userLocation);
        });
    }
}

function onPickupChange() {
    const place = pickupAutocomplete.getPlace();
    if (place.geometry) {
        pickupLocation = {
            lat: place.geometry.location.lat(),
            lng: place.geometry.location.lng(),
            address: place.formatted_address
        };
        map.setCenter(place.geometry.location);
        new google.maps.Marker({
            position: place.geometry.location,
            map: map,
            label: 'P',
            title: 'Pickup'
        });
    }
}

function onDestinationChange() {
    const place = destinationAutocomplete.getPlace();
    if (place.geometry) {
        destinationLocation = {
            lat: place.geometry.location.lat(),
            lng: place.geometry.location.lng(),
            address: place.formatted_address
        };
    }
}

function calculateFare() {
    if (!pickupLocation || !destinationLocation) {
        alert('Please select both pickup and destination locations');
        return;
    }
    
    const request = {
        origin: pickupLocation,
        destination: destinationLocation,
        travelMode: 'DRIVING'
    };
    
    directionsService.route(request, function(result, status) {
        if (status == 'OK') {
            directionsRenderer.setDirections(result);
            
            const distance = result.routes[0].legs[0].distance.value / 1000;
            const duration = result.routes[0].legs[0].duration.value / 60;
            const rideType = document.getElementById('rideType').value;
            
            let baseFare = 500;
            let perKmRate = 150;
            let perMinuteRate = 20;
            
            if (rideType === 'premium') {
                baseFare = 800;
                perKmRate = 200;
                perMinuteRate = 30;
            } else if (rideType === 'suv') {
                baseFare = 1000;
                perKmRate = 250;
                perMinuteRate = 40;
            }
            
            const fare = baseFare + (distance * perKmRate) + (duration * perMinuteRate) + 50;
            
            document.getElementById('estimatedFare').textContent = Math.round(fare);
            document.getElementById('distance').textContent = distance.toFixed(2);
            document.getElementById('duration').textContent = Math.round(duration);
            document.getElementById('fareEstimate').classList.remove('hidden');
            document.getElementById('bookBtn').disabled = false;
        }
    });
}

async function bookRide() {
    const bookBtn = document.getElementById('bookBtn');
    bookBtn.disabled = true;
    bookBtn.textContent = 'Booking...';
    
    const fare = parseFloat(document.getElementById('estimatedFare').textContent);
    const distance = parseFloat(document.getElementById('distance').textContent);
    const duration = parseFloat(document.getElementById('duration').textContent);
    
    const bookingData = {
        pickup_location: pickupLocation,
        dropoff_location: destinationLocation,
        distance: distance,
        duration: duration,
        fare: fare,
        ride_type: document.getElementById('rideType').value
    };
    
    try {
        const response = await fetch('/api/student/book/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(bookingData)
        });
        
        if (response.ok) {
            const data = await response.json();
            showNotification('Success', 'Ride booked successfully! Looking for a driver...');
            startTripTracking(data.trip_id);
        } else {
            const error = await response.json();
            showNotification('Error', error.message || 'Failed to book ride');
            bookBtn.disabled = false;
            bookBtn.textContent = 'Book Now';
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error', 'Network error. Please try again.');
        bookBtn.disabled = false;
        bookBtn.textContent = 'Book Now';
    }
}

function startTripTracking(tripId) {
    // Connect to WebSocket for trip updates
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/trip/${tripId}/`);
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        updateTripStatus(data);
    };
    
    // Start polling for driver location
    if (watchPositionId) {
        navigator.geolocation.clearWatch(watchPositionId);
    }
    
    watchPositionId = navigator.geolocation.watchPosition(
        updateStudentLocation,
        console.error,
        { enableHighAccuracy: true }
    );
}

function updateTripStatus(data) {
    const tripSection = document.getElementById('activeTripSection');
    const tripDetails = document.getElementById('tripDetails');
    
    if (!tripSection.classList.contains('hidden')) {
        tripSection.classList.remove('hidden');
    }
    
    let statusHtml = `
        <div class="space-y-4">
            <div class="flex justify-between items-center">
                <span class="font-semibold">Status:</span>
                <span class="px-3 py-1 rounded-full text-sm ${getStatusColor(data.status)}">
                    ${data.status_display}
                </span>
            </div>
    `;
    
    if (data.driver) {
        statusHtml += `
            <div class="p-4 bg-gray-50 rounded-lg">
                <p class="font-semibold mb-2">Driver Details:</p>
                <div class="flex items-center">
                    <div class="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-white mr-3">
                        ${data.driver.name.charAt(0)}
                    </div>
                    <div>
                        <p class="font-medium">${data.driver.name}</p>
                        <p class="text-sm text-gray-600">Rating: ${data.driver.rating || 'New'}</p>
                        <p class="text-sm text-gray-600">${data.vehicle?.make || ''} ${data.vehicle?.model || ''}</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    statusHtml += `
            <div>
                <p class="font-semibold">Pickup:</p>
                <p class="text-gray-600">${data.pickup_address}</p>
            </div>
            <div>
                <p class="font-semibold">Destination:</p>
                <p class="text-gray-600">${data.dropoff_address}</p>
            </div>
            <div>
                <p class="font-semibold">Fare:</p>
                <p class="text-2xl font-bold text-blue-600">₦${data.fare}</p>
            </div>
    `;
    
    if (data.status === 'searching' || data.status === 'accepted') {
        statusHtml += `
            <button onclick="cancelTrip(${data.id})" 
                    class="w-full bg-red-600 text-white py-2 rounded-lg hover:bg-red-700">
                Cancel Trip
            </button>
        `;
    }
    
    statusHtml += `</div>`;
    tripDetails.innerHTML = statusHtml;
}

function getStatusColor(status) {
    const colors = {
        'searching': 'bg-yellow-100 text-yellow-800',
        'accepted': 'bg-blue-100 text-blue-800',
        'arrived': 'bg-green-100 text-green-800',
        'ongoing': 'bg-purple-100 text-purple-800',
        'completed': 'bg-gray-100 text-gray-800',
        'cancelled': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
}

async function cancelTrip(tripId) {
    if (!confirm('Are you sure you want to cancel this trip?')) return;
    
    try {
        const response = await fetch(`/api/trips/${tripId}/cancel/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        if (response.ok) {
            showNotification('Success', 'Trip cancelled successfully');
            location.reload();
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error', 'Failed to cancel trip');
    }
}

async function updateStudentLocation(position) {
    const locationData = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        heading: position.coords.heading,
        speed: position.coords.speed
    };
    
    try {
        await fetch('/api/student/location/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(locationData)
        });
    } catch (error) {
        console.error('Failed to update location:', error);
    }
}

async function fetchNearbyDrivers() {
    if (!pickupLocation) return;
    
    try {
        const response = await fetch(`/api/student/nearby-drivers/?lat=${pickupLocation.lat}&lng=${pickupLocation.lng}`);
        const drivers = await response.json();
        
        const driversContainer = document.getElementById('nearbyDrivers');
        if (drivers.length === 0) {
            driversContainer.innerHTML = '<p class="col-span-full text-center text-gray-500">No nearby drivers available</p>';
            return;
        }
        
        driversContainer.innerHTML = drivers.map(driver => `
            <div class="border rounded-lg p-4 hover:shadow-lg transition">
                <div class="flex items-center mb-3">
                    <div class="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-white mr-3">
                        ${driver.name.charAt(0)}
                    </div>
                    <div>
                        <p class="font-medium">${driver.name}</p>
                        <p class="text-sm text-yellow-600">★ ${driver.rating || 'New'}</p>
                    </div>
                </div>
                ${driver.vehicle ? `
                    <p class="text-sm text-gray-600">
                        ${driver.vehicle.make} ${driver.vehicle.model} • ${driver.vehicle.color}
                    </p>
                ` : ''}
                <p class="text-xs text-gray-500 mt-2">
                    ${driver.distance_km ? driver.distance_km.toFixed(1) : '~'} km away
                </p>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error fetching drivers:', error);
    }
}

// Top up functions
function topupWallet() {
    document.getElementById('topupModal').classList.remove('hidden');
}

function closeTopupModal() {
    document.getElementById('topupModal').classList.add('hidden');
}

async function processTopup() {
    const amount = document.getElementById('topupAmount').value;
    if (!amount || amount < 100) {
        alert('Please enter a valid amount (minimum ₦100)');
        return;
    }
    
    try {
        const response = await fetch('/api/student/topup/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ amount: parseFloat(amount) })
        });
        
        if (response.ok) {
            showNotification('Success', 'Wallet topped up successfully');
            location.reload();
        } else {
            const error = await response.json();
            showNotification('Error', error.message);
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error', 'Failed to top up wallet');
    }
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    setInterval(fetchNearbyDrivers, 30000); // Update every 30 seconds
    fetchNearbyDrivers();
});