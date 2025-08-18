import { useState } from 'react';
import DataImportExport from './DataImportExport';
import NewDealForm from './NewDealForm';
import { geocode }      from './utils/geocode';
import './App.css';

export default function App() {
  // start stores as null, not empty array
  //in_hk = true; // assume we're in Hong Kong for geocoding
  const [filterdate,setFilterdate] = useState();
  const [query, setQuery]     = useState('');
  const [loading, setLoading]     = useState(false);
  const [stores, setStores] = useState([]);
  const [page, setPage] = useState(1);
  const [error,  setError]  = useState(null);
  const [filterType, setFilterType] = useState('');
  const types = ['全部', '寫字樓', '工商', '商舖', '車位', '辦公室','住宅單位','別墅','公寓','廠房','倉庫','土地'];
  const storetypes = ['寫字樓', '工商', '商舖', '車位', '辦公室','廠房','倉庫']
  const housetypes = ['住宅單位','別墅','公寓','土地']
  function findType(input) {
  if (storetypes.includes(input)) {
    return 'business';
  } else if (housetypes.includes(input)) {
    return 'house';
  } else {
    return ''; // or 'unknown'
  }
}
  const fetchStores = async (addr, pg = 1) => {
    if (!addr) return;
    // reset to null while loading
    setStores(null);
    setPage(pg);

    const params = new URLSearchParams({ address: addr, page: pg, limit: 10 });
    const res = await fetch(`${import.meta.env.VITE_API_URL}/stores?${params}`);
    if (!res.ok) {
      setStores([]); // mark “no results”
      return;
    }
    const { stores: list } = await res.json();
    setStores(list);
  };

  async function handleSearch(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    console.log('filterType is:', JSON.stringify(filterType));// For debugging
    // 1) Geocode the text query
    let coords;
    try {
      if (!query.trim()) {
        throw new Error('Please enter a location');
      }
      coords = await geocode(query.trim());
      if (!coords) {
        throw new Error(`Could not find location “${query.trim()}”`);
      }
    } catch (err) {
      setError(err.message);
      setStores([]);
      setLoading(false);
      return;
    }

    // 2) Build the API URL with params
    const params = new URLSearchParams({
      lat:      coords.lat,
      lng:      coords.lng,
      radius:   '5000',
      page:     '1',
      perPage:  '10'
    });
    if (filterType) {
      params.append('type', filterType);
    }
    if (filterdate){
      params.append('dateRange',filterdate);
    }
    const type = findType(filterType);
    let url;
    if (type === '') {
      // Show all results
      url = `${import.meta.env.VITE_API_URL}/api/search/all?${params.toString()}`;
    } else {
      // Redirect to specific type
      url = `${import.meta.env.VITE_API_URL}/api/search/all?${params.toString()}&type=${type}`;
    }
    console.log('Sending request to:', url);

    // 3) Fetch and set the results
    try {
      console.log('Search Params:', { query, filterType, filterdate });
      console.log('Making fetch request to:', url);
      const res = await fetch(url);
      console.log('Response status:', res.status);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        console.error('Response error:', body);
        throw new Error(body.error || `Server returned ${res.status}`);
      }
      const data = await res.json();
      console.log('Response data:', data);
      if (data.success && data.data) {
        console.log('Setting stores with data.data:', data.data.length, 'items');
        setStores(data.data);
      } else {
        console.log('Setting stores with fallback:', data.data || data || []);
        setStores(data.data || data || []);
      }
      } catch (err) {
        console.error('Fetch error:', err);
        setError(err.message);
        setStores([]);
      } finally {
        setLoading(false);
      }
    };

  return (
    <div className="bauhaus-container">
      {/* Header Section */}
      <header className="bauhaus-header">
        <div className="header-geometric">
          <div className="red-circle"></div>
          <div className="blue-square"></div>
          <div className="yellow-triangle"></div>
        </div>
        <h1 className="bauhaus-title">PROPERTY FINDER</h1>
        <div className="header-line"></div>
      </header>

      {/* Search Section */}
      <section className="search-section">
        <div className="search-grid">
          <form onSubmit={handleSearch} className="search-form">
            <div className="input-group">
              <label className="bauhaus-label">LOCATION</label>
              <input
                placeholder="Enter place name or address"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="bauhaus-input"
              />
            </div>
            
            <div className="filter-group">
              <div className="filter-item">
                <label className="bauhaus-label">TYPE</label>
                <select
                  value={filterType}
                  onChange={e => setFilterType(e.target.value)}
                  className="bauhaus-select"
                >
                  {types.map(t => (
                    <option key={t} value={t === '全部' ? '' : t}>{t}</option>
                  ))}
                </select>
              </div>
              
              <div className="filter-item">
                <label className="bauhaus-label">DATE RANGE</label>
                <select
                  value={filterdate}
                  onChange={e => setFilterdate(e.target.value)}
                  className="bauhaus-select"
                >
                  <option value="">全部</option>
                  <option value="30">最近30天</option>
                  <option value="60">最近60天</option>
                  <option value="90">最近90天</option>
                  <option value="180">最近半年</option>
                  <option value="365">最近一年</option>
                  <option value="730">最近两年</option>
                </select>
              </div>
            </div>
            
            <button type="submit" className="bauhaus-button">
              <span>SEARCH</span>
              <div className="button-accent"></div>
            </button>
          </form>
        </div>
      </section>

      {/* Tools Section */}
      <section className="tools-section">
        <div className="tools-grid">
          <div className="tool-card red-accent">
            <h3>DATA IMPORT</h3>
            <DataImportExport />
          </div>
          
          <div className="tool-card blue-accent">
            <h3>NEW DEAL</h3>
            <NewDealForm onSuccess={() => fetchStores(query, page)} />
          </div>
        </div>
      </section>

      {/* Results Section */}
      {loading && (
        <div className="loading-section">
          <div className="loading-geometric">
            <div className="loading-circle"></div>
            <div className="loading-square"></div>
            <div className="loading-triangle"></div>
          </div>
          <p>SEARCHING...</p>
        </div>
      )}

      {error && (
        <div className="error-section">
          <div className="error-accent"></div>
          <p>{error}</p>
        </div>
      )}

      {stores?.length > 0 && (
        <section className="results-section">
          <div className="results-header">
            <h2>RESULTS</h2>
            <div className="results-count">{stores.length} PROPERTIES</div>
          </div>
          
          <div className="results-grid">
            {stores.map((store, index) => (
              <article key={`${store.deal_type}-${store.id}`} className={`result-card ${index % 3 === 0 ? 'accent-red' : index % 3 === 1 ? 'accent-blue' : 'accent-yellow'}`}>
                <div className="card-header">
                  <div className="type-badge">
                    {types.includes(store.type) ? store.type : '未知'}
                  </div>
                  <div className="distance-badge">
                    {Math.round(store.distance)}M
                  </div>
                </div>
                
                <div className="property-name">
                  {store.building_name_zh || store.estate_name_zh || 'UNNAMED PROPERTY'}
                </div>
                
                <div className="property-details">
                  {store.flat && <span>座 {store.flat}</span>}
                  {store.floor && <span>樓 {store.floor}</span>}
                  {store.unit && <span>單位 {store.unit}</span>}
                </div>
                
                <div className="price-section">
                  <div className="price">HK$ {Number(store.deal_price).toLocaleString()}</div>
                  <div className="area">{store.area} SQ FT</div>
                </div>
                
                <div className="date-section">
                  {new Date(store.deal_date).toLocaleDateString()}
                </div>
                
                <div className="location-section">
                  <div>{store.province} {store.city}</div>
                  <div>{store.town} {store.street}</div>
                </div>
                
                {store.developer && (
                  <div className="developer-section">
                    DEVELOPER: {store.developer}
                  </div>
                )}
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}