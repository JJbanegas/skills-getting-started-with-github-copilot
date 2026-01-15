document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Display activities with participants
      displayActivities(activities);

      // Populate dropdown select
      Object.keys(activities).forEach(name => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  function displayActivities(activitiesData) {
    const activitiesList = document.getElementById('activities-list');
    activitiesList.innerHTML = '';

    for (const [activityName, activityData] of Object.entries(activitiesData)) {
      const activityCard = document.createElement('div');
      activityCard.className = 'activity-card';
      
      const participants = activityData.participants || [];
      const participantsHTML = participants.length > 0
        ? participants.map(p => `<li><span class="participant-name">${p}</span><button class="delete-btn" data-activity="${activityName}" data-email="${p}" aria-label="Remove participant">🗑️</button></li>`).join('')
        : '<li class="empty">No participants yet</li>';

      activityCard.innerHTML = `
        <h4>${activityName}</h4>
        <p><strong>Description:</strong> ${activityData.description}</p>
        <p><strong>Schedule:</strong> ${activityData.schedule}</p>
        <p><strong>Capacity:</strong> ${activityData.participants.length}/${activityData.max_participants}</p>
        <div class="participants-section">
          <h5>Participants:</h5>
          <ul class="participants-list">
            ${participantsHTML}
          </ul>
        </div>
      `;
      
      activitiesList.appendChild(activityCard);
      
      // Add event listeners to delete buttons
      const deleteButtons = activityCard.querySelectorAll('.delete-btn');
      deleteButtons.forEach(btn => {
        btn.addEventListener('click', handleDeleteParticipant);
      });
    }
  }

  async function handleDeleteParticipant(event) {
    event.preventDefault();
    const btn = event.target;
    const activity = btn.dataset.activity;
    const email = btn.dataset.email;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      if (response.ok) {
        messageDiv.textContent = `${email} has been unregistered from ${activity}.`;
        messageDiv.className = "success";
        messageDiv.classList.remove("hidden");
        
        // Refresh activities list
        fetchActivities();
        
        // Hide message after 5 seconds
        setTimeout(() => {
          messageDiv.classList.add("hidden");
        }, 5000);
      } else {
        const result = await response.json();
        messageDiv.textContent = result.detail || "Failed to unregister participant.";
        messageDiv.className = "error";
        messageDiv.classList.remove("hidden");
      }
    } catch (error) {
      messageDiv.textContent = "Failed to unregister participant. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering participant:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
