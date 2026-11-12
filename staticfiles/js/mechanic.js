// Mechanic Earnings
const monthlyEarnings = [
  { month: "May", earnings: 55000 },
  { month: "June", earnings: 60000 },
  { month: "July", earnings: 34000 },
  { month: "August", earnings: 45000 },
  { month: "September", earnings: 20000 },
  { month: "October", earnings: 65000 },
];

const ctx = document.getElementById("earning-chart");
new Chart(ctx, {
  type: "bar",
  data: {
    labels: monthlyEarnings.map((item) => item.month),
    datasets: [
      {
        label: "Monthly Earnings",
        data: monthlyEarnings.map((item) => item.earnings),
        backgroundColor: "rgba(0, 123, 255, 0.2)",
        borderColor: "rgba(0, 123, 255, 1)",
        borderWidth: 1,
      },
    ],
  },
  options: { scales: { y: { beginAtZero: true } } },
});
