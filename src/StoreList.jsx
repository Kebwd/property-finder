// src/components/StoreList.jsx
import { useState, useEffect } from 'react';

export default function StoreList({
  apiUrl,
  searchAddress,
  page,
  storesPerPage,
  onPrev,
  onNext,
}) {
  // local state holds the fetched stores
  const [stores, setStores] = useState([]);

  useEffect(() => {
    console.log(`Fetching page=${page}, address="${searchAddress}"`);
    if (!searchAddress) {
      setStores([]);
      return;
    }

    const url = `${apiUrl}/stores`
      + `?address=${encodeURIComponent(searchAddress)}`
      + `&page=${page}`
      + `&perPage=${storesPerPage}`;

    fetch(url)
      .then((res) => res.json())
      .then(data => {
        const list = Array.isArray(data) ? data : data.rows;
        setStores(Array.isArray(list) ? list : []);
    })
      .catch(err => console.error('Fetch error:', err));
  }, [apiUrl, searchAddress, page, storesPerPage]);

  return (
    <div className="space-y-4">
      {stores.map((store) => {
        // format date
        const dateStr = store.deal_date
          ? new Date(store.deal_date).toLocaleDateString()
          : '—';

        // parse the API’s string into a number, then format as currency
        const priceStr =
          store.deal_price != null
            ? Number(store.deal_price).toLocaleString(undefined, {
                style: 'currency',
                currency: 'HKD',
                minimumFractionDigits: 2
              })
            : '—';

        // distance is already in meters? convert to km
        const distStr =
          typeof store.distance === 'number'
            ? `${(store.distance / 1000).toFixed(2)} km`
            : '—';

        return (
          <div
            key={store.id}
            className="bg-white p-4 rounded shadow flex justify-between items-center"
          >
            <div>
              <h3 className="text-xl font-semibold">
                {store.name || '—'}
              </h3>
              <p className="text-gray-600">
                {store.address || '—'}
              </p>
              <p className="text-gray-700">
                {dateStr} — {priceStr}
              </p>
            </div>
            <span className="text-sm text-gray-500">
              {distStr}
            </span>
          </div>
        );
      })}

      {/* Pagination */}
      <div className="flex justify-center items-center space-x-4">
        <button
          onClick={onPrev}
          disabled={page <= 1}
          className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
        >
          Prev
        </button>
        <span>Page {page}</span>
        <button
          onClick={onNext}
          disabled={StoreList.length < 10}
          className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}