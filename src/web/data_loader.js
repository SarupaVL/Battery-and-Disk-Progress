/**
 * Battery & Disk Data Loader - Windows File-Based Integration
 * Reads battery and disk data from JSON files
 * Written by background service: battery_service.py
 */

class DataLoader {
  constructor() {
    this.batterySubscribers = [];
    this.diskSubscribers = [];
    this.batteryData = null;
    this.diskData = null;
    this.fetchInterval = null;
  }

  /**
   * Subscribe to battery data updates
   */
  subscribeBattery(callback) {
    this.batterySubscribers.push(callback);
    if (this.batteryData) {
      callback(this.batteryData);
    }
  }

  /**
   * Subscribe to disk data updates
   */
  subscribeDisk(callback) {
    this.diskSubscribers.push(callback);
    if (this.diskData) {
      callback(this.diskData);
    }
  }

  /**
   * Notify battery subscribers
   */
  notifyBatterySubscribers() {
    if (this.batteryData) {
      this.batterySubscribers.forEach(callback => {
        try {
          callback(this.batteryData);
        } catch (error) {
          console.error("Error in battery subscriber:", error);
        }
      });
    }
  }

  /**
   * Notify disk subscribers
   */
  notifyDiskSubscribers() {
    if (this.diskData) {
      this.diskSubscribers.forEach(callback => {
        try {
          callback(this.diskData);
        } catch (error) {
          console.error("Error in disk subscriber:", error);
        }
      });
    }
  }

  /**
   * Fetch battery data from JSON file
   */
  async fetchBatteryData() {
    try {
      const response = await fetch(`/data/battery_data.json?t=${Date.now()}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      this.batteryData = await response.json();
      this.notifyBatterySubscribers();
      return true;
    } catch (error) {
      console.warn(`⚠️ Cannot load battery_data.json: ${error.message}`);
      return false;
    }
  }

  /**
   * Fetch disk data from JSON file
   */
  async fetchDiskData() {
    try {
      const response = await fetch(`/data/disk_data.json?t=${Date.now()}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      this.diskData = await response.json();
      this.notifyDiskSubscribers();
      return true;
    } catch (error) {
      console.warn(`⚠️ Cannot load disk_data.json: ${error.message}`);
      return false;
    }
  }

  /**
   * Fetch both battery and disk data from the new live API endpoint
   */
  async fetchData() {
    try {
      const response = await fetch(`/api/live?t=${Date.now()}`);
      if (!response.ok) {
        if (response.status === 401) {
            console.warn("🔐 Unauthorized: Please login to view live metrics.");
            this.stop();
            return false;
        }
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.battery) {
        this.batteryData = data.battery;
        this.notifyBatterySubscribers();
      }
      
      if (data.disk) {
        this.diskData = data.disk;
        this.notifyDiskSubscribers();
      }
      
      return true;
    } catch (error) {
      console.warn(`⚠️ Live API Error: ${error.message}`);
      return false;
    }
  }

  /**
   * Start polling for data
   */
  start(interval = 2000) {
    if (this.fetchInterval) return;
    
    console.log("🚀 Data loader started");
    
    // Fetch immediately
    this.fetchData();
    
    // Then fetch at intervals
    this.fetchInterval = setInterval(() => {
      this.fetchData();
    }, interval);
  }

  /**
   * Stop polling
   */
  stop() {
    if (!this.fetchInterval) return;
    clearInterval(this.fetchInterval);
    this.fetchInterval = null;
    console.log("🛑 Data loader stopped");
  }
}

// Global instance
const dataLoader = new DataLoader();

// Auto-start
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    dataLoader.start(2000);
  });
} else {
  dataLoader.start(2000);
}
