document
    .getElementById("loginForm")
    .addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();

            const username =
                document.getElementById("username").value;

            const password =
                document.getElementById("password").value;

            const errorMessage =
                document.getElementById("errorMessage");

            errorMessage.textContent = "";

            try {

                const response =
                    await fetch(
                        "/api/login",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json"
                            },
                            credentials: "same-origin",
                            body: JSON.stringify({
                                username,
                                password
                            })
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        "Login failed"
                    );
                }

                window.location.href =
                    data.redirect;

            } catch (error) {

                errorMessage.textContent =
                    error.message;
            }
        }
    );

document
    .getElementById("registerBtn")
    .addEventListener(
        "click",
        async () => {

            const username =
                document.getElementById(
                    "username"
                ).value;

            const password =
                document.getElementById(
                    "password"
                ).value;

            try {

                const response =
                    await fetch(
                        "/api/register",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json"
                            },
                            body: JSON.stringify({
                                username,
                                password
                            })
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        "Registration failed"
                    );
                }

                alert(
                    `Account created successfully!\n\n` +
                    `Your User ID is ${data.user_id}\n` +
                    `Please write it down.`
                );

            } catch (err) {

                document
                    .getElementById(
                        "errorMessage"
                    )
                    .textContent =
                        err.message;
            }
        }
    );