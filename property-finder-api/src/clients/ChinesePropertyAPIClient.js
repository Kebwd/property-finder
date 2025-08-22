const axios = require('axios');

/**
 * Universal Chinese Property API Client
 * Supports multiple providers with standardized interface
 */
class ChinesePropertyAPIClient {
  constructor(config) {
    this.providers = config.providers || {};
    this.defaultProvider = config.defaultProvider || 'rapidapi';
    this.cache = new Map();
    this.cacheTimeout = config.cacheTimeout || 3600000; // 1 hour
  }

  /**
   * Get properties for a specific city from any provider
   */
  async getPropertiesByCity(city, options = {}) {
    const provider = options.provider || this.defaultProvider;
    const limit = options.limit || 50;
    const offset = options.offset || 0;

    console.log(`🔍 Fetching properties for ${city} from ${provider}`);

    try {
      // Check cache first
      const cacheKey = `${provider}-${city}-${limit}-${offset}`;
      if (this.cache.has(cacheKey)) {
        const cached = this.cache.get(cacheKey);
        if (Date.now() - cached.timestamp < this.cacheTimeout) {
          console.log(`📋 Using cached data for ${city}`);
          return cached.data;
        }
      }

      let apiData;
      switch (provider) {
        case 'rapidapi':
          apiData = await this.fetchFromRapidAPI(city, limit, offset);
          break;
        case 'fang':
          apiData = await this.fetchFromFang(city, limit, offset);
          break;
        case 'anjuke':
          apiData = await this.fetchFromAnjuke(city, limit, offset);
          break;
        case 'government':
          apiData = await this.fetchFromGovernment(city, limit, offset);
          break;
        default:
          throw new Error(`Unknown provider: ${provider}`);
      }

      // Standardize the data format
      const standardizedData = this.standardizePropertyData(apiData, provider);

      // Cache the results
      this.cache.set(cacheKey, {
        data: standardizedData,
        timestamp: Date.now()
      });

      console.log(`✅ Retrieved ${standardizedData.length} properties from ${provider}`);
      return standardizedData;

    } catch (error) {
      console.error(`❌ Error fetching from ${provider}:`, error.message);
      
      // Try fallback provider if available
      if (options.allowFallback !== false) {
        const fallbackProviders = Object.keys(this.providers).filter(p => p !== provider);
        if (fallbackProviders.length > 0) {
          console.log(`🔄 Trying fallback provider: ${fallbackProviders[0]}`);
          return this.getPropertiesByCity(city, {
            ...options,
            provider: fallbackProviders[0],
            allowFallback: false
          });
        }
      }
      
      throw error;
    }
  }

  /**
   * RapidAPI Provider Integration
   */
  async fetchFromRapidAPI(city, limit, offset) {
    const config = this.providers.rapidapi;
    if (!config) throw new Error('RapidAPI configuration not found');

    const options = {
      method: 'GET',
      url: `${config.baseUrl}/properties`,
      params: {
        city: this.getCityCode(city),
        limit,
        offset,
        country: 'CN'
      },
      headers: {
        'X-RapidAPI-Key': config.apiKey,
        'X-RapidAPI-Host': config.host
      }
    };

    const response = await axios.request(options);
    return response.data;
  }

  /**
   * Fang.com API Integration
   */
  async fetchFromFang(city, limit, offset) {
    const config = this.providers.fang;
    if (!config) throw new Error('Fang API configuration not found');

    const options = {
      method: 'GET',
      url: `${config.baseUrl}/openapi/ershoufang/list`,
      params: {
        city: this.getCityCode(city),
        pageSize: limit,
        pageNo: Math.floor(offset / limit) + 1,
        appkey: config.appKey
      },
      headers: {
        'Authorization': `Bearer ${config.token}`,
        'Content-Type': 'application/json'
      }
    };

    const response = await axios.request(options);
    return response.data;
  }

  /**
   * Anjuke API Integration
   */
  async fetchFromAnjuke(city, limit, offset) {
    const config = this.providers.anjuke;
    if (!config) throw new Error('Anjuke API configuration not found');

    const options = {
      method: 'POST',
      url: `${config.baseUrl}/api/property/search`,
      data: {
        city_id: this.getCityCode(city),
        limit,
        offset,
        property_type: 'residential'
      },
      headers: {
        'API-Key': config.apiKey,
        'Content-Type': 'application/json'
      }
    };

    const response = await axios.request(options);
    return response.data;
  }

  /**
   * Government Open Data Integration
   */
  async fetchFromGovernment(city, limit, offset) {
    const config = this.providers.government;
    if (!config) throw new Error('Government API configuration not found');

    // Government APIs vary by city
    const cityConfig = config.cities[city];
    if (!cityConfig) throw new Error(`Government API not available for ${city}`);

    const options = {
      method: 'GET',
      url: cityConfig.endpoint,
      params: {
        limit,
        offset,
        format: 'json'
      }
    };

    const response = await axios.request(options);
    return response.data;
  }

  /**
   * Standardize property data from different providers
   */
  standardizePropertyData(apiData, provider) {
    const properties = this.extractPropertiesArray(apiData, provider);
    
    return properties.map(property => {
      try {
        return {
          building_name_zh: this.extractBuildingName(property, provider),
          deal_price: this.extractPrice(property, provider),
          area: this.extractArea(property, provider),
          location: this.extractLocation(property, provider),
          zone: 'China',
          city: this.extractCity(property, provider),
          province: this.extractProvince(property, provider),
          type_raw: this.extractType(property, provider),
          type: this.extractType(property, provider),
          deal_date: this.extractDate(property, provider),
          source_url: this.extractSourceUrl(property, provider),
          data_source: this.getProviderName(provider),
          scraped_city: this.extractCity(property, provider),
          start_url: this.extractSourceUrl(property, provider)
        };
      } catch (error) {
        console.warn(`⚠️ Error standardizing property from ${provider}:`, error.message);
        return null;
      }
    }).filter(property => property !== null);
  }

  /**
   * Extract properties array from different API response formats
   */
  extractPropertiesArray(apiData, provider) {
    switch (provider) {
      case 'rapidapi':
        return apiData.properties || apiData.data || apiData.results || [];
      case 'fang':
        return apiData.data?.list || apiData.result?.list || [];
      case 'anjuke':
        return apiData.data?.properties || apiData.properties || [];
      case 'government':
        return apiData.data || apiData.records || [];
      default:
        return Array.isArray(apiData) ? apiData : [];
    }
  }

  /**
   * Provider-specific field extraction methods
   */
  extractBuildingName(property, provider) {
    const fields = {
      rapidapi: ['title', 'name', 'property_name'],
      fang: ['title', 'xiaoqu_name', 'community_name'],
      anjuke: ['title', 'community_name', 'property_title'],
      government: ['building_name', 'property_name', 'title']
    };

    return this.getFirstValidField(property, fields[provider] || ['title', 'name']);
  }

  extractPrice(property, provider) {
    const priceFields = {
      rapidapi: ['price', 'total_price', 'price_total'],
      fang: ['total_price', 'price', 'zongjia'],
      anjuke: ['price', 'total_price', 'price_wan'],
      government: ['deal_price', 'transaction_price', 'price']
    };

    const price = this.getFirstValidField(property, priceFields[provider] || ['price']);
    return this.normalizePrice(price, provider);
  }

  extractArea(property, provider) {
    const areaFields = {
      rapidapi: ['area', 'size', 'square_meters'],
      fang: ['mianji', 'area', 'jianzhu_mianji'],
      anjuke: ['area', 'building_area', 'size'],
      government: ['area', 'building_area', 'size']
    };

    const area = this.getFirstValidField(property, areaFields[provider] || ['area']);
    return parseFloat(area) || 0;
  }

  extractLocation(property, provider) {
    const locationFields = {
      rapidapi: ['address', 'location', 'full_address'],
      fang: ['address', 'quyu_name', 'district'],
      anjuke: ['address', 'district_name', 'location'],
      government: ['address', 'location', 'district']
    };

    return this.getFirstValidField(property, locationFields[provider] || ['address', 'location']);
  }

  extractCity(property, provider) {
    const cityFields = {
      rapidapi: ['city', 'city_name'],
      fang: ['city_name', 'city'],
      anjuke: ['city_name', 'city'],
      government: ['city', 'city_name']
    };

    return this.getFirstValidField(property, cityFields[provider] || ['city']);
  }

  extractProvince(property, provider) {
    const provinceFields = {
      rapidapi: ['province', 'state', 'region'],
      fang: ['province_name', 'province'],
      anjuke: ['province_name', 'province'],
      government: ['province', 'region']
    };

    return this.getFirstValidField(property, provinceFields[provider] || ['province']);
  }

  extractType(property, provider) {
    const typeFields = {
      rapidapi: ['property_type', 'type', 'category'],
      fang: ['fangwu_type', 'house_type', 'type'],
      anjuke: ['property_type', 'house_type', 'type'],
      government: ['property_type', 'building_type', 'type']
    };

    const type = this.getFirstValidField(property, typeFields[provider] || ['type']);
    return this.normalizePropertyType(type);
  }

  extractDate(property, provider) {
    const dateFields = {
      rapidapi: ['date', 'listed_date', 'created_at'],
      fang: ['deal_date', 'chengjiao_date', 'update_time'],
      anjuke: ['deal_date', 'update_time', 'created_at'],
      government: ['transaction_date', 'deal_date', 'date']
    };

    const date = this.getFirstValidField(property, dateFields[provider] || ['date']);
    return this.normalizeDate(date);
  }

  extractSourceUrl(property, provider) {
    const urlFields = {
      rapidapi: ['url', 'source_url', 'link'],
      fang: ['url', 'detail_url', 'link'],
      anjuke: ['url', 'property_url', 'link'],
      government: ['source_url', 'url', 'link']
    };

    return this.getFirstValidField(property, urlFields[provider] || ['url', 'link']);
  }

  /**
   * Utility methods
   */
  getFirstValidField(obj, fields) {
    for (const field of fields) {
      if (obj && obj[field] !== undefined && obj[field] !== null && obj[field] !== '') {
        return obj[field];
      }
    }
    return '';
  }

  normalizePrice(price, provider) {
    if (!price) return 0;
    
    // Convert string prices to numbers
    if (typeof price === 'string') {
      // Handle Chinese price formats
      if (price.includes('万')) {
        const match = price.match(/(\d+\.?\d*)/);
        return match ? parseInt(parseFloat(match[1]) * 10000) : 0;
      }
      
      // Extract numbers from string
      const match = price.match(/(\d+\.?\d*)/);
      return match ? parseInt(parseFloat(match[1])) : 0;
    }
    
    return parseInt(price) || 0;
  }

  normalizePropertyType(type) {
    if (!type) return '住宅';
    
    const typeMapping = {
      'residential': '住宅',
      'apartment': '公寓',
      'villa': '别墅',
      'commercial': '商业',
      'office': '写字楼'
    };
    
    return typeMapping[type.toLowerCase()] || type;
  }

  normalizeDate(date) {
    if (!date) return new Date().toISOString().split('T')[0];
    
    try {
      return new Date(date).toISOString().split('T')[0];
    } catch {
      return new Date().toISOString().split('T')[0];
    }
  }

  getCityCode(city) {
    const cityCodes = {
      'beijing': 'bj',
      'shanghai': 'sh',
      'shenzhen': 'sz',
      'guangzhou': 'gz',
      'foshan': 'fs',
      'dongguan': 'dg'
    };
    
    return cityCodes[city.toLowerCase()] || city;
  }

  getProviderName(provider) {
    const names = {
      'rapidapi': 'RapidAPI Provider',
      'fang': '房天下',
      'anjuke': '安居客',
      'government': '政府数据'
    };
    
    return names[provider] || provider;
  }

  /**
   * Get provider statistics
   */
  getProviderStats() {
    const stats = {};
    for (const [key, value] of this.cache.entries()) {
      const provider = key.split('-')[0];
      if (!stats[provider]) {
        stats[provider] = { requests: 0, properties: 0 };
      }
      stats[provider].requests++;
      stats[provider].properties += value.data.length;
    }
    return stats;
  }
}

module.exports = ChinesePropertyAPIClient;
