import random
import json
from datetime import datetime, timedelta
import os

class ChinesePropertyDataGenerator:
    """Generate realistic Chinese property data for testing and development"""
    
    def __init__(self):
        # City configurations with realistic price ranges (per sqm)
        self.cities = {
            # Tier 1 Cities (一线城市)
            'beijing': {
                'name_zh': '北京',
                'province': '北京市',
                'price_range': (50000, 120000),  # per sqm
                'districts': ['朝阳区', '海淀区', '西城区', '东城区', '丰台区', '石景山区']
            },
            'shanghai': {
                'name_zh': '上海',
                'province': '上海市', 
                'price_range': (45000, 110000),
                'districts': ['黄浦区', '徐汇区', '长宁区', '静安区', '普陀区', '虹口区']
            },
            'shenzhen': {
                'name_zh': '深圳',
                'province': '广东省',
                'price_range': (40000, 100000),
                'districts': ['南山区', '福田区', '罗湖区', '宝安区', '龙岗区', '盐田区']
            },
            'guangzhou': {
                'name_zh': '广州',
                'province': '广东省',
                'price_range': (25000, 60000),
                'districts': ['天河区', '越秀区', '荔湾区', '海珠区', '白云区', '黄埔区']
            },
            
            # Tier 2 Cities (二线城市) - Guangdong Province
            'foshan': {
                'name_zh': '佛山',
                'province': '广东省',
                'price_range': (15000, 35000),
                'districts': ['禅城区', '南海区', '顺德区', '三水区', '高明区']
            },
            'dongguan': {
                'name_zh': '东莞',
                'province': '广东省',
                'price_range': (18000, 40000),
                'districts': ['南城区', '东城区', '万江区', '莞城区', '石碣镇']
            },
            'zhuhai': {
                'name_zh': '珠海',
                'province': '广东省',
                'price_range': (20000, 45000),
                'districts': ['香洲区', '斗门区', '金湾区']
            },
            'zhongshan': {
                'name_zh': '中山',
                'province': '广东省',
                'price_range': (12000, 28000),
                'districts': ['石岐区', '东区', '西区', '南区', '火炬开发区']
            },
            'jiangmen': {
                'name_zh': '江门',
                'province': '广东省',
                'price_range': (8000, 18000),
                'districts': ['蓬江区', '江海区', '新会区']
            },
            'huizhou': {
                'name_zh': '惠州',
                'province': '广东省',
                'price_range': (10000, 25000),
                'districts': ['惠城区', '惠阳区', '大亚湾区']
            },
            
            # Other Major Cities
            'chongqing': {
                'name_zh': '重庆',
                'province': '重庆市',
                'price_range': (8000, 20000),
                'districts': ['渝中区', '江北区', '南岸区', '九龙坡区', '沙坪坝区']
            },
            'wuhan': {
                'name_zh': '武汉',
                'province': '湖北省',
                'price_range': (12000, 30000),
                'districts': ['江汉区', '硚口区', '汉阳区', '武昌区', '青山区']
            },
            'xiamen': {
                'name_zh': '厦门',
                'province': '福建省',
                'price_range': (25000, 50000),
                'districts': ['思明区', '湖里区', '集美区', '海沧区']
            },
            'fuzhou': {
                'name_zh': '福州',
                'province': '福建省',
                'price_range': (15000, 35000),
                'districts': ['鼓楼区', '台江区', '仓山区', '晋安区', '马尾区']
            },
            'quanzhou': {
                'name_zh': '泉州',
                'province': '福建省',
                'price_range': (10000, 25000),
                'districts': ['鲤城区', '丰泽区', '洛江区', '泉港区']
            }
        }
        
        # Property types
        self.property_types = [
            '住宅', '公寓', '别墅', '商住两用', '四合院', '平房', '复式', '跃层'
        ]
        
        # Building name patterns
        self.building_patterns = [
            '{district}{number}号院',
            '{district}花园',
            '{district}小区',
            '{district}公馆',
            '{district}府邸',
            '{district}雅苑',
            '{district}豪庭',
            '{district}新城',
            '{district}广场',
            '{district}中心'
        ]
    
    def generate_city_data(self, city_key, num_properties=50):
        """Generate property data for a specific city"""
        if city_key not in self.cities:
            raise ValueError(f"City {city_key} not supported")
        
        city_config = self.cities[city_key]
        properties = []
        
        for i in range(num_properties):
            property_data = self._generate_single_property(city_key, city_config)
            properties.append(property_data)
        
        return properties
    
    def _generate_single_property(self, city_key, city_config):
        """Generate a single property record"""
        # Random district
        district = random.choice(city_config['districts'])
        
        # Generate building name
        building_pattern = random.choice(self.building_patterns)
        building_name = building_pattern.format(
            district=district,
            number=random.randint(1, 99)
        )
        
        # Property specifications
        area = round(random.uniform(50, 200), 1)  # 50-200 sqm
        price_per_sqm = random.randint(*city_config['price_range'])
        total_price = int(area * price_per_sqm)
        
        # Property type
        property_type = random.choice(self.property_types)
        
        # Generate deal date (within last 6 months)
        days_ago = random.randint(1, 180)
        deal_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        return {
            'building_name_zh': building_name,
            'deal_price': total_price,
            'area': area,
            'location': f"{city_config['name_zh']}{district}",
            'zone': 'China',
            'city': city_config['name_zh'],
            'province': city_config['province'],
            'type_raw': property_type,
            'type': [property_type],
            'deal_date': deal_date,
            'source_url': f'https://demo.property-finder.com/{city_key}',
            'data_source': 'Demo Data Generator',
            'scraped_city': city_key,
            'start_url': f'https://demo.property-finder.com/{city_key}',
            'price_per_sqm': price_per_sqm,
            'district': district,
            'bedrooms': random.randint(1, 4),
            'bathrooms': random.randint(1, 3),
            'floor': f"{random.randint(1, 30)}/{random.randint(30, 40)}",
            'building_year': random.randint(2000, 2023),
            'orientation': random.choice(['南向', '南北通透', '东南向', '西南向', '东向', '西向']),
            'decoration': random.choice(['精装修', '简装修', '毛坯', '豪华装修'])
        }
    
    def generate_all_cities_data(self, properties_per_city=30):
        """Generate data for all configured cities"""
        all_data = {}
        
        print("🏗️  GENERATING DEMO PROPERTY DATA")
        print("=" * 50)
        
        for city_key in self.cities.keys():
            print(f"📊 Generating {properties_per_city} properties for {self.cities[city_key]['name_zh']}...")
            all_data[city_key] = self.generate_city_data(city_key, properties_per_city)
        
        return all_data
    
    def save_to_json(self, data, filename='chinese_property_demo_data.json'):
        """Save generated data to JSON file"""
        output_path = os.path.join(os.path.dirname(__file__), filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Data saved to: {output_path}")
        return output_path
    
    def generate_summary(self, data):
        """Generate summary statistics"""
        total_properties = sum(len(city_data) for city_data in data.values())
        
        print(f"\n📈 DEMO DATA SUMMARY")
        print("=" * 30)
        print(f"🏙️  Total Cities: {len(data)}")
        print(f"🏘️  Total Properties: {total_properties}")
        print(f"💰 Price Range: {self._get_price_range(data)}")
        
        # City breakdown
        for city_key, properties in data.items():
            city_name = self.cities[city_key]['name_zh']
            avg_price = sum(p['deal_price'] for p in properties) / len(properties)
            print(f"   {city_name}: {len(properties)} properties (平均价格: ¥{avg_price:,.0f})")
    
    def _get_price_range(self, data):
        """Calculate overall price range"""
        all_prices = []
        for city_data in data.values():
            all_prices.extend([p['deal_price'] for p in city_data])
        
        if all_prices:
            return f"¥{min(all_prices):,} - ¥{max(all_prices):,}"
        return "N/A"

def main():
    """Generate demo data for all Chinese cities"""
    generator = ChinesePropertyDataGenerator()
    
    # Generate data for all cities
    all_data = generator.generate_all_cities_data(properties_per_city=40)
    
    # Save to JSON
    output_file = generator.save_to_json(all_data)
    
    # Generate summary
    generator.generate_summary(all_data)
    
    print(f"\n✅ DEMO DATA GENERATION COMPLETE")
    print(f"📁 Output file: {output_file}")
    print(f"🎯 Use this data while working on real scraping solutions")

if __name__ == "__main__":
    main()
