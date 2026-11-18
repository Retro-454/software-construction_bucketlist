document.getElementById("loginForm")
    .addEventListener("submit", async function(event) {

        event.preventDefault();

        const username =
            document.getElementById("username").value;

        const password =
            document.getElementById("password").value;

        const errorMessage =
            document.getElementById("errorMessage");

        errorMessage.textContent = "";

        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "same-origin",
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Login failed");
            }

            // Redirect to task dashboard
            window.location.href = data.redirect;

        } catch (error) {
            errorMessage.textContent = error.message;
        }
    });