// DOM Elements
const driverAcct = document.getElementById("driver");
const mechanicAcct = document.getElementById("mechanic");
const formGroup = document.querySelector(".form-group");
const driverForm = document.getElementById("DriverForm");
const mechanicForm = document.getElementById("MechanicForm");
let driverFormHeight = driverForm.offsetHeight;
let mechanicFormHeight = mechanicForm.offsetHeight;
// Set the height of the formGroup container to be the height of driverForm
formGroup.style.height =
  document.getElementById("DriverForm").offsetHeight + "px";

// To display form based on the account type selected
function checkAccountType() {
  if (driverAcct.checked) {
    formGroup.style.height =
      document.getElementById("DriverForm").offsetHeight + "px";
    driverForm.classList.add("active");
    mechanicForm.classList.remove("active");
  } else {
    formGroup.style.height =
      document.getElementById("MechanicForm").offsetHeight + "px";
    driverForm.classList.remove("active");
    mechanicForm.classList.add("active");
  }
}
driver.onchange = checkAccountType;
mechanic.onchange = checkAccountType;

// Toggle Password visibility
const visibilityBtns = document.querySelectorAll(".show-password");
visibilityBtns.forEach((btn, index) => {
  btn.addEventListener("click", () => {
    const password = document.getElementById(`password${index + 1}`); // for password1 and password2 IDs
    if (password.getAttribute("type") === "password") {
      password.setAttribute("type", "text");
      btn.innerHTML = '<i class="fa fa-eye-slash"></i> Hide';
    } else {
      password.setAttribute("type", "password");
      btn.innerHTML = '<i class="fa fa-eye"></i> Show';
    }
  });
});

// To fix overflow issue When toggled from a desktop to a mobile view
window.addEventListener("resize", () => {
  // checking which form is currently displayed
  if (driverForm.classList.contains("active")) {
    formGroup.style.height =
      document.getElementById("DriverForm").offsetHeight + "px";
  } else {
    formGroup.style.height =
      document.getElementById("MechanicForm").offsetHeight + "px";
  }
});
