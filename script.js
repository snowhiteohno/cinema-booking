const container = document.querySelector('.container');
const seatArea = document.getElementById('seat-area');
const count = document.getElementById('count');
const total = document.getElementById('total');
const movieSelect = document.getElementById('movie');
const bookBtn = document.getElementById('bookBtn');

let ticketPrice = +movieSelect.value;

const rows = 6;
const seatsPerRow = 8;

const occupiedSeats = [10, 11, 24, 25, 26, 38, 39, 45, 46];

function generateSeats() {
  seatArea.innerHTML = ''; 

  for (let i = 0; i < rows; i++) {
    const rowDiv = document.createElement('div');
    rowDiv.classList.add('row');

    for (let j = 0; j < seatsPerRow; j++) {
      const seatIndex = (i * seatsPerRow) + j;
      const seatDiv = document.createElement('div');
      
      seatDiv.classList.add('seat');
      
      if (occupiedSeats.includes(seatIndex)) {
        seatDiv.classList.add('occupied');
      }

      rowDiv.appendChild(seatDiv);
    }
    seatArea.appendChild(rowDiv);
  }
}

function updateSelectedCount() {
  const selectedSeats = document.querySelectorAll('.row .seat.selected');
  const selectedSeatsCount = selectedSeats.length;

  count.innerText = selectedSeatsCount;
  total.innerText = selectedSeatsCount * ticketPrice;
}

movieSelect.addEventListener('change', (e) => {
  ticketPrice = +e.target.value;
  updateSelectedCount();
});

seatArea.addEventListener('click', (e) => {
  if (
    e.target.classList.contains('seat') && 
    !e.target.classList.contains('occupied')
  ) {
    e.target.classList.toggle('selected');
    updateSelectedCount();
  }
});

bookBtn.addEventListener('click', () => {
    const selectedSeats = document.querySelectorAll('.row .seat.selected').length;
    if(selectedSeats > 0) {
        alert(`You have booked ${selectedSeats} tickets!`);
    } else {
        alert('Please select a seat first.');
    }
});

generateSeats();
updateSelectedCount();