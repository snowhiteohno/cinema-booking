# Pastel Cinema Booking UI

## Project Overview
This project is a lightweight, frontend-only Movie Seat Booking interface. It demonstrates how to build a responsive, interactive user interface using **Vanilla HTML, CSS, and JavaScript** without any external libraries or frameworks.

The primary goal of this project was to solve a specific UI/UX problem: poor visibility of seat states in dark mode interfaces.

---

## How It Works

1.  **Movie Selection:**
    * The user selects a movie from the dropdown menu.
    * The JavaScript updates the `ticketPrice` variable dynamically based on the selection.
2.  **Seat Generation:**
    * On page load, the JavaScript loop generates a grid of seats (divs) inside the container.
    * It checks against a hardcoded array of `occupiedSeats` to assign the "occupied" class to specific seats.
3.  **Interaction:**
    * **Clicking a Seat:** The user clicks a seat. If it is not occupied, it toggles the `.selected` class.
    * **Visual Feedback:** The seat changes color and glows to indicate selection.
    * **Data Update:** The total count of selected seats and the total price are recalculated and displayed instantly.
4.  **Booking:**
    * Clicking the "Book Tickets" button verifies if seats are selected and provides an alert confirmation.

---

## Design Decisions & Requirement Fulfillment

This project was engineered to meet specific design constraints regarding accessibility and aesthetics.

### 1. Requirement: "Clearly Differentiable Seat States"
**The Problem:** In many dark-mode apps, "Available" (Grey) and "Occupied" (Dark Grey) look too similar.
**The Solution:** We used a **Tri-Factor differentiation approach** (Color, Opacity, and Form).

* **Available:** * *Color:* Pastel Cyan.
    * *Behavior:* High opacity, scales up on hover.
* **Selected:** * *Color:* Pastel Yellow.
    * *Behavior:* Emits a glow (`box-shadow`), identifying it as the active element.
* **Occupied:** * *Color:* Pastel Red.
    * *Behavior:* Low Opacity (0.4) and `cursor: not-allowed`. It visually recedes into the background, signalling it cannot be interacted with.

### 2. Requirement: "Pastel Color Theme"
**The Problem:** Neon colors on dark backgrounds can cause eye strain.
**The Solution:** We utilized a specific "Soft Light" pastel palette defined in CSS variables.

| State | Color Name | Hex Code | Visual Logic |
| :--- | :--- | :--- | :--- |
| **Available** | `Pastel Cyan` | `#9BF6FF` | Cool, neutral, inviting. |
| **Selected** | `Pastel Yellow` | `#FDFFB6` | Brightest value, demands attention. |
| **Occupied** | `Pastel Red` | `#FFADAD` | Universal "Stop" signal, but desaturated to be soft. |
| **Background** | `Dark Blue-Grey`| `#2B2D42` | Provides contrast without the harshness of pure black. |

### 3. Requirement: "Pure HTML/CSS/JS (No Frameworks)"
**The Solution:**
* **HTML:** Semantic structure only. No inline styles.
* **CSS:** Handles all visuals, including the 3D perspective of the screen and hover animations.
* **JS:** Handles logic only (DOM manipulation, Event Delegation for performance, and Math).

---

## File Structure

To run this project, ensure your folder is organized as follows:

```text
/MovieBookingProject
│
├── index.html    # The skeleton (DOM structure)
├── style.css     # The skin (Pastel theme, animations, layout)
├── script.js     # The brain (Logic, pricing, seat generation)
└── README.md     # This documentation
