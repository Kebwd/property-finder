import express from 'express';
import { Pool } from 'pg';
import XLSX from 'xlsx';

const router = express.Router();
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

router.get('/', async (req, res, next) => {
  let client;
  try {
    client = await pool.connect();

    // Get both business and house data separately and combine
    const businessQuery = `
      SELECT
        'business' as record_type,
        l.province as "省",
        l.city as "市",
        l.country as "區",
        l.town as "街道",
        l.street as "街道",
        l.road as "路",
        b.type as "物業類別",
        b.building_name_zh as "大廈名稱",
        '' as "座數",
        b.floor as "樓層",
        b.unit as "單位",
        b.area as "實用面積（平方呎）",
        b.deal_price as "成交價格",
        to_char(b.deal_date, 'DD/MM/YYYY') as "成交日期",
        b.developer as "發展商",
        '' as "房屋類型",
        '' as "屋苑名稱",
        '' as "座"
      FROM location_info l
      JOIN business b ON l.id = b.location_id
      ORDER BY b.deal_date DESC
    `;

    const houseQuery = `
      SELECT
        'house' as record_type,
        l.province as "省",
        l.city as "市", 
        l.country as "區",
        l.town as "街道",
        l.street as "街道",
        l.road as "路",
        h.type as "物業類別",
        h.building_name_zh as "大廈名稱",
        h.flat as "座數",
        h.floor as "樓層",
        h.unit as "單位",
        h.area as "實用面積（平方呎）",
        h.deal_price as "成交價格",
        to_char(h.deal_date, 'DD/MM/YYYY') as "成交日期",
        h.developer as "發展商",
        h.house_type as "房屋類型",
        h.estate_name_zh as "屋苑名稱",
        h.flat as "座"
      FROM location_info l
      JOIN house h ON l.id = h.location_id
      ORDER BY h.deal_date DESC
    `;

    const [businessResult, houseResult] = await Promise.all([
      client.query(businessQuery),
      client.query(houseQuery)
    ]);

    // Combine both datasets
    const combinedData = [
      ...businessResult.rows,
      ...houseResult.rows
    ].sort((a, b) => new Date(b.成交日期) - new Date(a.成交日期));

    // Create workbook
    const workbook = XLSX.utils.book_new();

    // Create main data sheet
    const mainSheet = XLSX.utils.json_to_sheet(combinedData, {
      header: [
        "省", "市", "區", "街道", "路", "物業類別", "屋苑名稱", "座", "大廈名稱", 
        "樓層", "單位", "實用面積（平方呎）", "成交價格", "成交日期", "發展商", "房屋類型"
      ]
    });

    // Set column widths for better readability
    const columnWidths = [
      { wch: 8 },   // 省
      { wch: 10 },  // 市
      { wch: 10 },  // 區
      { wch: 15 },  // 街道
      { wch: 15 },  // 路
      { wch: 12 },  // 物業類別
      { wch: 20 },  // 屋苑名稱
      { wch: 8 },   // 座
      { wch: 20 },  // 大廈名稱
      { wch: 8 },   // 樓層
      { wch: 8 },   // 單位
      { wch: 18 },  // 實用面積
      { wch: 15 },  // 成交價格
      { wch: 12 },  // 成交日期
      { wch: 15 },  // 發展商
      { wch: 12 }   // 房屋類型
    ];
    
    mainSheet['!cols'] = columnWidths;

    // Add header styling
    const headerRange = XLSX.utils.decode_range(mainSheet['!ref']);
    for (let col = headerRange.s.c; col <= headerRange.e.c; col++) {
      const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col });
      if (!mainSheet[cellAddress]) continue;
      
      mainSheet[cellAddress].s = {
        font: { bold: true, color: { rgb: "FFFFFF" } },
        fill: { fgColor: { rgb: "366092" } },
        alignment: { horizontal: "center", vertical: "center" }
      };
    }

    // Append the main sheet
    XLSX.utils.book_append_sheet(workbook, mainSheet, '物業成交記錄');

    // Create separate sheets for business and house data
    if (businessResult.rows.length > 0) {
      const businessSheet = XLSX.utils.json_to_sheet(businessResult.rows);
      businessSheet['!cols'] = columnWidths;
      XLSX.utils.book_append_sheet(workbook, businessSheet, '商業物業');
    }

    if (houseResult.rows.length > 0) {
      const houseSheet = XLSX.utils.json_to_sheet(houseResult.rows);
      houseSheet['!cols'] = columnWidths;
      XLSX.utils.book_append_sheet(workbook, houseSheet, '住宅物業');
    }

    // Generate Excel buffer
    const buffer = XLSX.write(workbook, { 
      type: 'buffer', 
      bookType: 'xlsx',
      cellStyles: true
    });

    // Set response headers
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', 'attachment; filename="property_transactions_' + new Date().toISOString().split('T')[0] + '.xlsx"');
    res.send(buffer);

    client.release();
  } catch (err) {
    console.error('Export error:', err);
    if (client) client.release();
    next(err);
  }
});

export default router;
