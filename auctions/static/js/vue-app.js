import Vue from 'vue';

new Vue({
  el: '#vue-content',
  data: {
    listings: [
      { id: 1, title: 'Item 1', price: '$100' },
      { id: 2, title: 'Item 2', price: '$200' },
      { id: 3, title: 'Item 3', price: '$300' }
    ]
  },
  template: `
    <div>
      <h2>Active Listings</h2>
      <ul class="list-group">
        <li class="list-group-item" v-for="listing in listings" :key="listing.id">
          {{ listing.title }} - {{ listing.price }}
        </li>
      </ul>
    </div>
  `
});
