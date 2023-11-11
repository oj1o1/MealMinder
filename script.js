document.addEventListener('DOMContentLoaded', function () {
    const navLinks = document.querySelectorAll('.navbar a'); // Select all navigation links
    const sections = document.querySelectorAll('section'); // Select all sections
    const homeSection = document.querySelector('.home'); // Select the home section

    // Function to update the active link based on the current section
    function updateActiveLink() {
        let scrollY = window.scrollY;

        sections.forEach((section, index) => {
            const sectionTop = section.offsetTop - 100; // Adjust for header height or any offset if needed
            const sectionBottom = sectionTop + section.clientHeight;

            if (scrollY >= sectionTop && scrollY <= sectionBottom) {
                // Remove the "active" class from all navigation links
                navLinks.forEach((link) => {
                    link.classList.remove('active');
                });

                // Add the "active" class to the corresponding navigation link
                navLinks[index].classList.add('active');

                // Transfer show-animate class from home section to active section
                homeSection.classList.remove('show-animate');
                section.classList.add('show-animate');
            }
        });
    }

    // Add scroll event listener to update the active link when scrolling
    window.addEventListener('scroll', updateActiveLink);

    // Initial check to set the active link on page load
    updateActiveLink();
});


document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('.form-main');

    form.addEventListener('submit', function (event) {
        event.preventDefault();

        const formData = new FormData(form);

        fetch('/plan_meal', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const mealPlanDiv = document.querySelector('.meal-plan');
            mealPlanDiv.innerHTML = '';

            if (data.recommended_foods) {
                const table = document.createElement('table');
                const headerRow = document.createElement('tr');
                const headers = ['Name', 'Serving', 'Calories'];

                headers.forEach(headerText => {
                    const th = document.createElement('th');
                    th.textContent = headerText;
                    headerRow.appendChild(th);
                });

                table.appendChild(headerRow);

                data.recommended_foods.forEach(food => {
                    const row = document.createElement('tr');

                    headers.forEach(header => {
                        const cell = document.createElement('td');
                        cell.textContent = food[header.toLowerCase()];
                        row.appendChild(cell);
                    });

                    table.appendChild(row);
                });

                mealPlanDiv.appendChild(table);

                const totalCaloriesElement = document.createElement('h2');
                totalCaloriesElement.textContent = 'Total Calories';
                mealPlanDiv.appendChild(totalCaloriesElement);

                const totalCaloriesValue = document.createElement('p');
                totalCaloriesValue.id = 'total-calories';
                totalCaloriesValue.textContent = `${data.total_calories} cal`;
                mealPlanDiv.appendChild(totalCaloriesValue);
            }
        });
    });
});
