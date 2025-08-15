// src/NewDealForm.jsx
import { useState } from 'react';

const BASE = import.meta.env.VITE_API_URL;  
console.log('API URL is:', import.meta.env.VITE_API_URL);
const businessTypes = ['寫字樓', '工商', '商舖', '車位', '辦公室', '廠房', '倉庫'];
const residentialTypes = ['住宅單位', '別墅', '公寓'];
const landTypes = ['土地'];

export default function NewDealForm({ onSuccess }) {
  const [isChina, setIsChina] = useState(false);
  const [dealDate, setDealDate] = useState('');
  const [price, setPrice] = useState('');
  const [type, setType] = useState('');
  
  // China location fields
  const [province, setProvince] = useState('');
  const [city, setCity] = useState('');
  const [district, setDistrict] = useState('');
  const [street, setStreet] = useState('');
  const [road, setRoad] = useState('');
  
  // House-specific fields
  const [estateName, setEstateName] = useState('');
  const [block, setBlock] = useState('');
  const [buildingName, setBuildingName] = useState('');
  const [floor, setFloor] = useState('');
  const [unit, setUnit] = useState('');
  const [area, setArea] = useState('');
  const [developer, setDeveloper] = useState('');
  
  const isResidentialType = residentialTypes.includes(type);
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Build location info for China
    let locationInfo = {};
    if (isChina) {
      locationInfo = {
        province,
        city,
        district,
        street,
        road
      };
    }
    
    // Build building info for both business and house types
    let buildingInfo = {};
    if (type) {
      buildingInfo = {
        block,
        building_name: buildingName,
        floor,
        unit,
        area: parseFloat(area) || null,
        developer
      };
      
      // Add residential-specific fields
      if (isResidentialType) {
        buildingInfo.estate_name = estateName;
      }
    }
    
    const payload = {
      deal_date: dealDate,
      deal_price: parseFloat(price),
      type,
      location_info: isChina ? locationInfo : null,
      building_info: type ? buildingInfo : null,
      region: isChina ? 'CN' : 'HK'
    };

    let res, data;
    try {
      // Choose endpoint based on type
      const endpoint = isResidentialType ? 'house' : 'business';
      res = await fetch(`${BASE}/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      data = await res.json();
    } catch (networkErr) {
      console.error('Network error:', networkErr);
      alert('Cannot reach API—check the URL in .env and server logs');
      return;
    }


    if (!res.ok) {
      console.error('API responded with error:', data.error || data);
      alert('Server error: ' + (data.error || res.statusText));
      return;
    }

    console.log('Created deal:', data);
    onSuccess();
    // Reset all fields
    setDealDate('');
    setPrice('');
    setType('');
    setProvince('');
    setCity('');
    setDistrict('');
    setStreet('');
    setRoad('');
    setEstateName('');
    setBlock('');
    setBuildingName('');
    setFloor('');
    setUnit('');
    setArea('');
    setDeveloper('');
  };

  return (
    <form onSubmit={handleSubmit} className="bauhaus-tool-content">
      <div className="form-grid">
        {/* Region Selection */}
        <div className="form-group full-width">
          <label className="bauhaus-label checkbox-label">
            <input
              type="checkbox"
              checked={isChina}
              onChange={(e) => setIsChina(e.target.checked)}
              className="bauhaus-checkbox"
            />
            <span className="checkbox-text">中國地區 (CHINA REGION)</span>
          </label>
        </div>

        {/* China Location Fields */}
        {isChina && (
          <>
            <div className="form-group">
              <label className="bauhaus-label">省 (PROVINCE)</label>
              <input
                type="text"
                value={province}
                onChange={(e) => setProvince(e.target.value)}
                className="bauhaus-input"
                placeholder="ENTER PROVINCE"
              />
            </div>
            <div className="form-group">
              <label className="bauhaus-label">市 (CITY)</label>
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="bauhaus-input"
                placeholder="ENTER CITY"
              />
            </div>
            <div className="form-group">
              <label className="bauhaus-label">區 (DISTRICT)</label>
              <input
                type="text"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className="bauhaus-input"
                placeholder="ENTER DISTRICT"
              />
            </div>
            <div className="form-group">
              <label className="bauhaus-label">街道 (STREET)</label>
              <input
                type="text"
                value={street}
                onChange={(e) => setStreet(e.target.value)}
                className="bauhaus-input"
                placeholder="ENTER STREET"
              />
            </div>
            <div className="form-group">
              <label className="bauhaus-label">路 (ROAD)</label>
              <input
                type="text"
                value={road}
                onChange={(e) => setRoad(e.target.value)}
                className="bauhaus-input"
                placeholder="ENTER ROAD"
              />
            </div>
          </>
        )}

        <div className="form-group">
          <label className="bauhaus-label">DEAL DATE</label>
          <input
            type="date"
            value={dealDate}
            onChange={(e) => setDealDate(e.target.value)}
            required
            className="bauhaus-input"
          />
        </div>

        <div className="form-group">
          <label className="bauhaus-label">TYPE</label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="bauhaus-select"
            required
          >
            <option value="">SELECT TYPE</option>
            <optgroup label="商業 (BUSINESS)">
              {businessTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </optgroup>
            <optgroup label="住宅 (RESIDENTIAL)">
              {residentialTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </optgroup>
            <optgroup label="土地 (LAND)">
              {landTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </optgroup>
          </select>
        </div>

        {/* Building fields - shown for both business and house types when type is selected */}
        {type && (
          <>
            {/* Estate Name - only for residential types */}
            {isResidentialType && (
              <div className="form-group">
                <label className="bauhaus-label">屋苑名稱 (ESTATE NAME)</label>
                <input
                  type="text"
                  value={estateName}
                  onChange={(e) => setEstateName(e.target.value)}
                  className="bauhaus-input"
                  placeholder="ENTER ESTATE NAME"
                />
              </div>
            )}
            
            <div className="form-group">
              <label className="bauhaus-label">座 (BLOCK)</label>
              <input
                type="text"
                value={block}
                onChange={(e) => setBlock(e.target.value)}
                className="bauhaus-input"
                placeholder="ENTER BLOCK"
              />
            </div>
            <div className="form-group">
              <label className="bauhaus-label">大廈名稱 (BUILDING NAME)</label>
              <input
                type="text"
                value={buildingName}
                onChange={(e) => setBuildingName(e.target.value)}
                className="bauhaus-input"
                placeholder="ENTER BUILDING NAME"
              />
            </div>
            <div className="form-group">
              <label className="bauhaus-label">樓層 (FLOOR)</label>
              <input
                type="text"
                value={floor}
                onChange={(e) => setFloor(e.target.value)}
                className="bauhaus-input"
                placeholder="ENTER FLOOR"
              />
            </div>
            <div className="form-group">
              <label className="bauhaus-label">單位 (UNIT)</label>
              <input
                type="text"
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className="bauhaus-input"
                placeholder="ENTER UNIT"
              />
            </div>
            
            <div className="form-group">
              <label className="bauhaus-label">實用面積（平方呎）(AREA SQ FT)</label>
              <input
                type="number"
                step="0.01"
                value={area}
                onChange={(e) => setArea(e.target.value)}
                className="bauhaus-input"
                placeholder="ENTER AREA"
              />
            </div>
            
            <div className="form-group">
              <label className="bauhaus-label">發展商 (DEVELOPER)</label>
              <input
                type="text"
                value={developer}
                onChange={(e) => setDeveloper(e.target.value)}
                className="bauhaus-input"
                placeholder="ENTER DEVELOPER"
              />
            </div>
          </>
        )}

        <div className="form-group">
          <label className="bauhaus-label">PRICE (HK$)</label>
          <input
            type="number"
            step="0.01"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            required
            className="bauhaus-input"
            placeholder="0.00"
          />
        </div>
      </div>

      <button
        type="submit"
        className="bauhaus-tool-button submit-button full-width"
      >
        <span>ADD DEAL</span>
        <div className="tool-button-accent yellow"></div>
      </button>
    </form>
  );
}