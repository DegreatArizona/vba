$(document).ready(function () {
    $("#historyTable").DataTable();
    $("#invoiceTable").DataTable();
    $("#notificationTable").DataTable();
  });


// const requestServiceForm = document.getElementById("requestServiceForm");
// const automaticAddressBtn = document.getElementById("automatic-address");
// const locationInput = document.getElementById("location");
// const manualAddressBtn = document.getElementById("manual-address");
// const errorMsg = document.getElementById("error-msg"); // Adjusted selector

// const apiKey = "YOUR_OPENCAGE_API_KEY"; // Replace with your OpenCage API Key

// function showAddressInput() {
//     locationInput.classList.add("active");
// }

// // When "Use Current Location" button is clicked
// automaticAddressBtn.addEventListener("click", () => {
//     if (navigator.geolocation) {
//         navigator.geolocation.getCurrentPosition(showPosition, showError);
//     } else {
//         errorMsg.innerHTML = "Geolocation is not supported by this browser.";
//         showAddressInput(); // Activate the location input
//     }
// });

// manualAddressBtn.addEventListener("click", showAddressInput);

// function showPosition(position) {
//     const lat = position.coords.latitude;
//     const lon = position.coords.longitude;

//     // Use the OpenCage API to reverse geocode the coordinates into an address
//     fetch(`https://api.opencagedata.com/geocode/v1/json?q=${lat}+${lon}&key=${apiKey}`)
//         .then(response => response.json())
//         .then(data => {
//             if (data.results && data.results.length > 0) {
//                 const address = data.results[0].formatted;
//                 locationInput.value = address; // Fill the input field with the address
//             } else {
//                 locationInput.value = "Address not found";
//             }
//             showAddressInput(); // Activate the location input after getting the address
//         })
//         .catch(error => {
//             errorMsg.innerHTML = "Error fetching location.";
//             console.error('Error fetching location:', error);
//             showAddressInput(); // Show input field in case of error
//         });
// }

// function showError(error) {
//     switch (error.code) {
//         case error.PERMISSION_DENIED:
//             errorMsg.innerHTML = "User denied the request for Geolocation.";
//             break;
//         case error.POSITION_UNAVAILABLE:
//             errorMsg.innerHTML = "Location information is unavailable.";
//             break;
//         case error.TIMEOUT:
//             errorMsg.innerHTML = "The request to get user location timed out.";
//             break;
//         case error.UNKNOWN_ERROR:
//             errorMsg.innerHTML = "An unknown error occurred.";
//             break;
//     }
//     showAddressInput(); // Show input field if geolocation fails
// }

//   const requestServiceForm = document.getElementById("requestServiceForm");
//   const automaticAddressBtn = document.getElementById("automatic-address");
//   const locationInput = document.getElementById("location");
//   const manualAddressBtn = document.getElementById("manual-address");
//   const errorMsg = document.getElementById("error-msg"); // Adjusted selector
  
//   function showAddressInput() {
//       locationInput.classList.add("active");
//   }
  
//   // When "Use Current Location" button is clicked
//   automaticAddressBtn.addEventListener("click", () => {
//       if (navigator.geolocation) {
//           navigator.geolocation.getCurrentPosition(showPosition, showError);
//       } else {
//           errorMsg.innerHTML = "Geolocation is not supported by this browser.";
//           showAddressInput(); // Activate the location input
//       }
//   });
  
//   manualAddressBtn.addEventListener("click", showAddressInput);
  
//   function showPosition(position) {
//       const lat = position.coords.latitude;
//       const lon = position.coords.longitude;
  
//       // Displaying latitude and longitude in the input field
//       locationInput.value = `Latitude: ${lat}, Longitude: ${lon}`;
//       showAddressInput(); // Activate the location input after getting coordinates
//   }
  
//   function showError(error) {
//       switch (error.code) {
//           case error.PERMISSION_DENIED:
//               errorMsg.innerHTML = "User denied the request for Geolocation.";
//               break;
//           case error.POSITION_UNAVAILABLE:
//               errorMsg.innerHTML = "Location information is unavailable.";
//               break;
//           case error.TIMEOUT:
//               errorMsg.innerHTML = "The request to get user location timed out.";
//               break;
//           case error.UNKNOWN_ERROR:
//               errorMsg.innerHTML = "An unknown error occurred.";
//               break;
//       }
//       showAddressInput(); // Show input field if geolocation fails
//   }
  

    const requestServiceForm = document.getElementById("requestServiceForm");
    const apiKey = "SYXVN59lbmpKfl8deljDXjHpArciOCOa"; // Add your TomTom API key here
    const automaticAddressBtn = document.getElementById("automatic-address");
    const locationInput = document.getElementById("location");
    const manualAddressBtn = document.getElementById("manual-address");
    const errorMsg = document.getElementById("error-msg"); // Adjusted selector

    function showAddressInput() {
        locationInput.classList.add("active");
    }

    // When "Use Current Location" button is clicked
    automaticAddressBtn.addEventListener("click", () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(showPosition, showError);
        } else {
            errorMsg.innerHTML = "Geolocation is not supported by this browser.";
            showAddressInput(); // Activate the location input
        }
    });

    manualAddressBtn.addEventListener("click", showAddressInput);

    function showPosition(position) {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;

        // TomTom Reverse Geocoding API call
        fetch(`https://api.tomtom.com/search/2/reverseGeocode/${lat},${lon}.json?key=${apiKey}`)
            .then(response => response.json())
            .then(data => {
                if (data.addresses && data.addresses.length > 0) {
                    const address = data.addresses[0].address.freeformAddress;
                    locationInput.value = address;
                } else {
                    locationInput.value = "Address not found";
                }
                showAddressInput(); // Activate the location input after getting address
            })
            .catch(error => {
                errorMsg.innerHTML = "Error fetching location.";
                console.error('Error fetching location:', error);
                showAddressInput(); // Show input field in case of error
            });
    }

    function showError(error) {
        switch (error.code) {
            case error.PERMISSION_DENIED:
                errorMsg.innerHTML = "User denied the request for Geolocation.";
                break;
            case error.POSITION_UNAVAILABLE:
                errorMsg.innerHTML = "Location information is unavailable.";
                break;
            case error.TIMEOUT:
                errorMsg.innerHTML = "The request to get user location timed out.";
                break;
            case error.UNKNOWN_ERROR:
                errorMsg.innerHTML = "An unknown error occurred.";
                break;
        }
        showAddressInput(); // Show input field if geolocation fails
    }

