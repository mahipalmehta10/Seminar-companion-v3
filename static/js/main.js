// static/main.js

console.log("Sanity check!");

// Get Stripe publishable key
fetch("/config")
.then((result) => { return result.json(); })
.then((data) => {
  // Initialize Stripe.js
  console.log(data);
  const stripe = Stripe(data.publicKey);

  // new
  // Event handler
  document.querySelector("#submitBtn").addEventListener("click", (e) => {
    // Get Checkout Session ID
    e.preventDefault();
    amount = document.querySelector("#amount").value;
    email = document.querySelector("#uemail").value;
    title = document.querySelector("#event").value;
    event_id = document.querySelector("#event_id").value;
    user_id = document.querySelector("#user_id").value;
    fetch("/create-checkout-session", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `amount=${amount}&email=${email}&title=${title}&event_id=${event_id}&user_id=${user_id}`,
    })
    .then((result) => { 
        console.log('result', result);
        return result.json(); })
    .then((data) => {
      console.log(data);
      return stripe.redirectToCheckout({sessionId: data.sessionId})
    })
    .then((res) => {
      console.log(res);
    });
  });
});