document.addEventListener("DOMContentLoaded", function () {
    const captureBtn = document.getElementById("captureBtn");
    const capturedImage = document.getElementById("capturedImage");
    const imageContainer = document.querySelector(".image-container");
    const descriptionText = document.getElementById("description");

    captureBtn.addEventListener("click", function () {
        captureBtn.innerHTML = "Processing...";
        captureBtn.disabled = true;

        fetch("/capture", { method: "POST" })
            .then(response => response.json())
            .then(data => {
                if (data.image_url) {
                    capturedImage.src = data.image_url;
                    imageContainer.style.display = "flex"; // Show image container
                } else {
                    imageContainer.style.display = "none"; // Hide if no image
                }

                descriptionText.innerText = data.description || "No description available.";
            })
            .catch(error => {
                console.error("Error:", error);
                descriptionText.innerText = "Error capturing image.";
            })
            .finally(() => {
                captureBtn.innerHTML = "<i class='fas fa-camera'></i> Capture Image";
                captureBtn.disabled = false;
            });
    });
});