import React, { useState, useEffect } from 'react';
import { ArrowRight, Sparkles, Building2, Package, CheckCircle, Shield } from 'lucide-react';

function App() {
  const [stage, setStage] = useState('intro');
  const [boothNumber, setBoothNumber] = useState('');
  const [isAnimating, setIsAnimating] = useState(true);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [introProgress, setIntroProgress] = useState(0);
  const [checklistData, setChecklistData] = useState({
    totalItems: 0,
    completedItems: 0,
    items: [],
    exhibitorName: '',
    section: ''
  });

  useEffect(() => {
    if (stage === 'intro') {
      const timer1 = setTimeout(() => setIntroProgress(1), 300);
      const timer2 = setTimeout(() => setIntroProgress(2), 1200);
      const timer3 = setTimeout(() => setIntroProgress(3), 2200);
      const timer4 = setTimeout(() => {
        setIntroProgress(4);
        setTimeout(() => setStage('welcome'), 1000);
      }, 3500);
      
      return () => {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
        clearTimeout(timer4);
      };
    }
  }, [stage]);

  useEffect(() => {
    if (stage === 'welcome') {
      const timer = setTimeout(() => {
        setIsAnimating(false);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [stage]);

  const orderStatuses = {
    'delivered': { 
      label: 'Delivered', 
      progress: 100, 
      color: 'from-green-500 to-emerald-500',
      icon: CheckCircle,
      bgColor: 'bg-green-500/20 text-green-400',
      priority: 5
    },
    'out-for-delivery': { 
      label: 'Out for Delivery', 
      progress: 75, 
      color: 'from-blue-500 to-cyan-500',
      icon: Package,
      bgColor: 'bg-blue-500/20 text-blue-400',
      priority: 3
    },
    'in-route': { 
      label: 'In Route from Warehouse', 
      progress: 50, 
      color: 'from-yellow-500 to-orange-500',
      icon: Building2,
      bgColor: 'bg-yellow-500/20 text-yellow-400',
      priority: 2
    },
    'in-process': { 
      label: 'In Process', 
      progress: 25, 
      color: 'from-purple-500 to-pink-500',
      icon: Shield,
      bgColor: 'bg-purple-500/20 text-purple-400',
      priority: 1
    },
    'cancelled': { 
      label: 'Cancelled', 
      progress: 0, 
      color: 'from-red-500 to-red-600',
      icon: ArrowRight,
      bgColor: 'bg-red-500/20 text-red-400',
      priority: 4
    }
  };

  const API_BASE = 'https://v3-exhibitor-live-update.onrender.com/api';

  // Fetch checklist data by booth number
  const fetchChecklistByBooth = async (boothNum) => {
    setLoading(true);
    try {
      console.log('Fetching checklist for booth:', boothNum);
      
      const response = await fetch(`${API_BASE}/checklist/booth/${encodeURIComponent(boothNum)}`);
      if (!response.ok) throw new Error('Failed to fetch checklist');
      
      const data = await response.json();
      console.log('Checklist Response:', data);
      
      setChecklistData({
        totalItems: data.total_items || 0,
        completedItems: data.completed_items || 0,
        items: data.items || [],
        exhibitorName: data.exhibitor_name || '',
        section: data.section || ''
      });
      
    } catch (error) {
      console.error('Error fetching checklist:', error);
      
      // Fallback checklist data for demo
      const fallbackChecklist = {
        totalItems: 12,
        completedItems: 8,
        exhibitorName: `Booth ${boothNum} Exhibitor`,
        section: 'Section 1',
        items: [
          { name: 'BeMatrix Structure with White Double Fabric Walls', quantity: 1, status: true, special_instructions: '' },
          { name: '3m x 4m Corner Booth', quantity: 1, status: true, special_instructions: '' },
          { name: 'Rectangular White Table', quantity: 1, status: true, special_instructions: '' },
          { name: 'White Chair', quantity: 4, status: true, special_instructions: '' },
          { name: 'One Time Vacuuming Prior to Opening', quantity: 100, status: true, special_instructions: '' },
          { name: 'Wastebasket', quantity: 1, status: true, special_instructions: 'Complimentary wastebasket' },
          { name: 'Company Name Sign 24"W x 16"H', quantity: 1, status: true, special_instructions: '' },
          { name: '500 Watt Electrical Outlet', quantity: 1, status: true, special_instructions: '' },
          { name: '6\' Track with Three Can Lights', quantity: 1, status: false, special_instructions: '' },
          { name: 'White Shelving Unit', quantity: 1, status: false, special_instructions: '' },
          { name: '3m x 4m Wood Vinyl Flooring', quantity: 1, status: false, special_instructions: '' },
          { name: '3M Fabric Graphic - 117.17"W x 95.20"H', quantity: 1, status: false, special_instructions: '' }
        ]
      };
      
      setChecklistData(fallbackChecklist);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrdersByBooth = async (boothNum) => {
    setLoading(true);
    try {
      console.log('Fetching orders for booth:', boothNum);
      
      const response = await fetch(`${API_BASE}/orders/booth/${encodeURIComponent(boothNum)}`);
      if (!response.ok) throw new Error('Failed to fetch orders');
      
      const data = await response.json();
      console.log('Orders Response:', data);
      
      setOrders(data.orders || []);
      generateNotifications(data.orders || []);
      
    } catch (error) {
      console.error('Error fetching orders:', error);
      
      const fallbackOrders = [
        {
          id: `ORD-${boothNum}-001`,
          item: 'Round Table 30" high',
          description: 'Professional exhibition furniture',
          booth_number: boothNum,
          color: 'White',
          quantity: 2,
          status: 'delivered',
          order_date: new Date().toLocaleDateString(),
          comments: 'Coordinated by Expo Convention Contractors',
          section: 'Section A'
        },
        {
          id: `ORD-${boothNum}-002`,
          item: 'White Side Chair',
          description: 'Professional seating solution',
          booth_number: boothNum,
          color: 'White',
          quantity: 4,
          status: 'out-for-delivery',
          order_date: new Date().toLocaleDateString(),
          comments: 'High-quality event furniture',
          section: 'Section A'
        }
      ];
      
      setOrders(fallbackOrders);
      generateNotifications(fallbackOrders);
    } finally {
      setLoading(false);
    }
  };

  const generateNotifications = (ordersData) => {
    const notifications = [];
    ordersData.forEach((order) => {
      if (order.status === 'in-route') {
        notifications.push({
          id: Math.random(),
          message: `${order.item} is in route from warehouse`,
          time: `${Math.floor(Math.random() * 30) + 1} min ago`,
          type: 'delivery'
        });
      } else if (order.status === 'delivered') {
        notifications.push({
          id: Math.random(),
          message: `${order.item} has been delivered`,
          time: `${Math.floor(Math.random() * 120) + 1} min ago`,
          type: 'success'
        });
      }
    });
    setNotifications(notifications.slice(0, 3));
  };

  const renderProgressBar = (status) => {
    const statusInfo = orderStatuses[status] || orderStatuses['in-process'];
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-700 font-medium">Delivery Progress</span>
          <span className="text-gray-900 font-bold">{statusInfo.progress}%</span>
        </div>
        <div className="relative w-full bg-gray-200 rounded-full h-3">
          <div 
            className={`bg-gradient-to-r ${statusInfo.color} h-3 rounded-full transition-all duration-1000`}
            style={{ width: `${statusInfo.progress}%` }}
          >
          </div>
        </div>
      </div>
    );
  };

  const ExpoLogo = ({ size = "large" }) => {
    return (
      <div className="flex items-center">
        <img 
          src="https://i.ibb.co/5gdgZVxj/output-onlinepngtools.png" 
          alt="Expo Convention Contractors"
          className={`${size === "large" ? "h-12 md:h-16" : "h-8"} w-auto object-contain`}
        />
      </div>
    );
  };

  const handleBoothSubmit = () => {
    if (boothNumber.trim()) {
      setStage('options');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleBoothSubmit();
    }
  };

  const handleOrdersClick = () => {
    setStage('orders');
    fetchOrdersByBooth(boothNumber);
  };

  const handleChecklistClick = () => {
    setStage('checklist');
    fetchChecklistByBooth(boothNumber);
  };

  if (stage === 'intro') {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center overflow-hidden">
        <div className="relative text-center">
          <div className={`transition-all duration-1000 ease-out ${
            introProgress >= 1 ? 'opacity-100' : 'opacity-0'
          } ${
            introProgress >= 4 ? 'opacity-0 translate-y-8 scale-95' : 'translate-y-0 scale-100'
          }`}>
            <div className="relative">
              <div className="flex justify-center">
                {['W', 'e', 'l', 'c', 'o', 'm', 'e'].map((letter, index) => (
                  <span
                    key={index}
                    className={`text-6xl md:text-8xl lg:text-9xl font-light text-black transition-all duration-700 ease-out ${
                      introProgress >= 2 && introProgress < 4 ? 'opacity-100 translate-y-0' : 'opacity-0'
                    } ${
                      introProgress < 2 ? 'translate-y-12' : 'translate-y-0'
                    }`}
                    style={{
                      transitionDelay: introProgress >= 2 && introProgress < 4 ? `${index * 120}ms` : '0ms',
                      fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", sans-serif',
                      letterSpacing: '-0.02em',
                      fontWeight: '300'
                    }}
                  >
                    {letter}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (stage === 'welcome') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-teal-100/40 rounded-full blur-3xl"></div>
          <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gray-100/60 rounded-full blur-3xl"></div>
          <div className="absolute top-1/2 right-1/3 w-48 h-48 bg-teal-50/60 rounded-full blur-3xl"></div>
        </div>

        <div className="relative min-h-screen flex items-center justify-center p-6">
          <div className="text-center max-w-md mx-auto w-full">
            
            <div className={`mb-8 transform transition-all duration-1000 ${isAnimating ? 'translate-y-10 opacity-0' : 'translate-y-0 opacity-100'}`}>
              <ExpoLogo size="large" />
            </div>

            <div className={`space-y-6 mb-12 transform transition-all duration-1000 delay-300 ${isAnimating ? 'translate-y-10 opacity-0' : 'translate-y-0 opacity-100'}`}>
              <h1 className="text-5xl md:text-6xl font-black text-gray-900 mb-4">
                ExpoFlow
              </h1>
              <p className="text-xl text-teal-600 font-medium mb-2">
                Order Tracking System
              </p>
              <div className="flex items-center justify-center space-x-2">
                <Building2 className="w-5 h-5 text-teal-600" />
                <span className="text-gray-600">Expo Convention Contractors</span>
              </div>
            </div>

            <div className={`transform transition-all duration-1000 delay-600 ${isAnimating ? 'translate-y-10 opacity-0' : 'translate-y-0 opacity-100'}`}>
              <div className="bg-white/90 backdrop-blur-lg rounded-3xl p-8 border border-gray-200 shadow-lg">
                
                <div className="space-y-6">
                  <div className="relative">
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      Enter Your Booth Number
                    </label>
                    <div className="relative">
                      <Building2 className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-teal-600" />
                      <input
                        type="text"
                        value={boothNumber}
                        onChange={(e) => setBoothNumber(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="e.g., A-123, B-456"
                        className="block w-full pl-10 pr-4 py-4 border border-gray-300 rounded-2xl leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent text-lg font-medium"
                        autoFocus
                      />
                    </div>
                  </div>

                  <button
                    onClick={handleBoothSubmit}
                    disabled={!boothNumber.trim()}
                    className={`w-full py-4 rounded-2xl font-semibold text-white transition-all duration-300 ${
                      boothNumber.trim()
                        ? 'bg-gradient-to-r from-teal-600 to-teal-700 hover:shadow-lg hover:scale-105'
                        : 'bg-gray-400 cursor-not-allowed'
                    }`}
                  >
                    <div className="flex items-center justify-center space-x-2">
                      <span>Continue</span>
                      <ArrowRight className="w-5 h-5" />
                    </div>
                  </button>
                </div>
              </div>
            </div>

            <div className={`mt-8 transform transition-all duration-1000 delay-900 ${isAnimating ? 'translate-y-10 opacity-0' : 'translate-y-0 opacity-100'}`}>
              <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
                <Shield className="w-4 h-4 text-green-500" />
                <span>System Online • Professional Exhibition Management</span>
              </div>
            </div>

          </div>
        </div>
      </div>
    );
  }

  if (stage === 'options') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-teal-100/40 rounded-full blur-3xl"></div>
          <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gray-100/60 rounded-full blur-3xl"></div>
          <div className="absolute top-1/2 right-1/3 w-48 h-48 bg-teal-50/60 rounded-full blur-3xl"></div>
        </div>

        <div className="relative min-h-screen flex items-center justify-center p-6">
          <div className="w-full max-w-5xl mx-auto">
            
            <div className="text-center mb-16">
              <div className="mb-6">
                <ExpoLogo size="large" />
              </div>
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                Choose your action
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
              
              <div className="group cursor-pointer transform transition-all duration-300 hover:scale-105" onClick={handleOrdersClick}>
                <div className="bg-white/90 backdrop-blur-lg rounded-3xl p-12 border border-gray-200 hover:border-teal-400 shadow-lg hover:shadow-xl transition-all duration-300 h-80 flex flex-col justify-center">
                  <div className="text-center">
                    <div className="w-28 h-28 bg-gradient-to-r from-teal-600 to-teal-700 rounded-3xl flex items-center justify-center mx-auto mb-8 group-hover:scale-110 transition-transform">
                      <Package className="w-14 h-14 text-white" />
                    </div>
                    <h3 className="text-3xl font-bold text-gray-900 mb-8">Orders</h3>
                    <div className="flex items-center justify-center space-x-3 text-teal-600 group-hover:text-teal-700 font-semibold text-lg">
                      <span>View Orders</span>
                      <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
                    </div>
                  </div>
                </div>
              </div>

              <div className="group cursor-pointer transform transition-all duration-300 hover:scale-105" onClick={handleChecklistClick}>
                <div className="bg-white/90 backdrop-blur-lg rounded-3xl p-12 border border-gray-200 hover:border-teal-400 shadow-lg hover:shadow-xl transition-all duration-300 h-80 flex flex-col justify-center">
                  <div className="text-center">
                    <div className="w-28 h-28 bg-gradient-to-r from-teal-600 to-teal-700 rounded-3xl flex items-center justify-center mx-auto mb-8 group-hover:scale-110 transition-transform">
                      <CheckCircle className="w-14 h-14 text-white" />
                    </div>
                    <h3 className="text-3xl font-bold text-gray-900 mb-8">Checklist</h3>
                    <div className="flex items-center justify-center space-x-3 text-teal-600 group-hover:text-teal-700 font-semibold text-lg">
                      <span>View Progress</span>
                      <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="text-center">
              <button
                onClick={() => setStage('welcome')}
                className="text-gray-600 hover:text-gray-900 py-3 px-6 rounded-2xl border border-gray-200 hover:bg-gray-50 transition-all duration-300"
              >
                ← Back to Booth Entry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Checklist Page - Beautiful Progress Visualization
  if (stage === 'checklist') {
    const progressPercentage = checklistData.totalItems > 0 
      ? Math.round((checklistData.completedItems / checklistData.totalItems) * 100) 
      : 0;
    
    const circumference = 2 * Math.PI * 90; // radius = 90
    const strokeDashoffset = circumference - (progressPercentage / 100) * circumference;

    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white p-6">
        <div className="max-w-7xl mx-auto">
          
          {/* Header */}
          <div className="bg-white/90 backdrop-blur-lg rounded-3xl p-4 md:p-6 border border-gray-200 shadow-xl mb-8">
            <div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0">
              
              <div className="flex items-center space-x-3 md:space-x-6">
                <div className="flex items-center space-x-3 md:space-x-4">
                  <ExpoLogo size="small" />
                  <div className="w-12 h-12 md:w-16 md:h-16 rounded-2xl bg-gradient-to-br from-teal-600 to-teal-700 flex items-center justify-center shadow-lg border border-gray-300">
                    <CheckCircle className="w-6 h-6 md:w-8 md:h-8 text-white" />
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <h1 className="text-xl md:text-3xl font-bold text-gray-900">Booth {boothNumber} Checklist</h1>
                  <p className="text-sm md:text-base text-gray-600">
                    <span className="text-teal-600">{checklistData.exhibitorName}</span>
                  </p>
                  <div className="flex flex-wrap items-center gap-2 md:gap-4 mt-1 md:mt-2">
                    <span className="text-xs md:text-sm text-teal-600 flex items-center space-x-1">
                      <Shield className="w-3 h-3 md:w-4 md:h-4" />
                      <span>{checklistData.section}</span>
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center justify-end space-x-2 md:space-x-4 flex-shrink-0">
                <button 
                  onClick={() => setStage('options')}
                  className="px-3 py-2 md:px-6 md:py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl md:rounded-2xl transition-all duration-300 border border-gray-200 text-sm md:text-base"
                >
                  ← Back
                </button>
              </div>
            </div>
          </div>

          {/* Progress Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            
            {/* Animated Circular Progress */}
            <div className="bg-white/90 backdrop-blur-lg rounded-3xl p-8 border border-gray-200 shadow-lg">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Booth Setup Progress</h2>
              
              <div className="relative flex items-center justify-center">
                <svg className="w-64 h-64 transform -rotate-90" viewBox="0 0 200 200">
                  {/* Background circle */}
                  <circle
                    cx="100"
                    cy="100"
                    r="90"
                    stroke="#e5e7eb"
                    strokeWidth="12"
                    fill="none"
                  />
                  {/* Progress circle */}
                  <circle
                    cx="100"
                    cy="100"
                    r="90"
                    stroke="url(#progressGradient)"
                    strokeWidth="12"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    className="transition-all duration-2000 ease-out"
                  />
                  {/* Gradient definition */}
                  <defs>
                    <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#059669" />
                      <stop offset="100%" stopColor="#10b981" />
                    </linearGradient>
                  </defs>
                </svg>
                
                {/* Center text */}
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                  <div className="text-4xl font-bold text-gray-900 mb-1">{progressPercentage}%</div>
                  <div className="text-gray-600 text-sm">Complete</div>
                  <div className="text-teal-600 text-xs mt-1">
                    {checklistData.completedItems} of {checklistData.totalItems} items
                  </div>
                </div>
              </div>
            </div>

            {/* Stats Cards */}
            <div className="space-y-6">
              <div className="bg-white/90 backdrop-blur-lg rounded-2xl p-6 border border-gray-200 shadow-lg">
                <div className="flex items-center space-x-3 mb-4">
                  <CheckCircle className="w-8 h-8 text-green-500" />
                  <h3 className="text-lg font-semibold text-gray-900">Completed Items</h3>
                </div>
                <div className="text-3xl font-bold text-green-500">{checklistData.completedItems}</div>
                <div className="text-xs text-gray-500 mt-1">Ready for show</div>
              </div>
              
              <div className="bg-white/90 backdrop-blur-lg rounded-2xl p-6 border border-gray-200 shadow-lg">
                <div className="flex items-center space-x-3 mb-4">
                  <Package className="w-8 h-8 text-orange-500" />
                  <h3 className="text-lg font-semibold text-gray-900">Pending Items</h3>
                </div>
                <div className="text-3xl font-bold text-orange-500">{checklistData.totalItems - checklistData.completedItems}</div>
                <div className="text-xs text-gray-500 mt-1">Being prepared</div>
              </div>
              
              <div className="bg-white/90 backdrop-blur-lg rounded-2xl p-6 border border-gray-200 shadow-lg">
                <div className="flex items-center space-x-3 mb-4">
                  <Building2 className="w-8 h-8 text-teal-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Total Items</h3>
                </div>
                <div className="text-3xl font-bold text-teal-600">{checklistData.totalItems}</div>
                <div className="text-xs text-gray-500 mt-1">For your booth</div>
              </div>
            </div>
          </div>

          {/* Loading state */}
          {loading && (
            <div className="text-center py-8">
              <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-700">Loading checklist from Expo CCI Database...</p>
            </div>
          )}

          {/* Detailed Items List */}
          {!loading && checklistData.items.length > 0 && (
            <div className="bg-white/90 backdrop-blur-lg rounded-2xl p-6 border border-gray-200 shadow-lg mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center space-x-2">
                <Sparkles className="w-6 h-6 text-teal-600" />
                <span>Booth Setup Items</span>
              </h2>
              
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {checklistData.items.map((item, index) => (
                  <div key={index} className={`flex items-center space-x-4 p-4 rounded-lg border transition-all duration-300 ${
                    item.status 
                      ? 'bg-green-50 border-green-200' 
                      : 'bg-orange-50 border-orange-200'
                  }`}>
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      item.status 
                        ? 'bg-green-500' 
                        : 'bg-orange-500'
                    }`}>
                      {item.status ? (
                        <CheckCircle className="w-4 h-4 text-white" />
                      ) : (
                        <Package className="w-4 h-4 text-white" />
                      )}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className={`font-semibold ${
                          item.status ? 'text-green-900' : 'text-orange-900'
                        }`}>
                          {item.name}
                        </h3>
                        <span className={`text-sm px-2 py-1 rounded-full ${
                          item.status 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-orange-100 text-orange-700'
                        }`}>
                          {item.status ? 'Ready' : 'Pending'}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-4 mt-1">
                        <span className={`text-sm ${
                          item.status ? 'text-green-600' : 'text-orange-600'
                        }`}>
                          Quantity: {item.quantity}
                        </span>
                        {item.special_instructions && (
                          <span className="text-xs text-gray-500 italic">
                            {item.special_instructions}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No items message */}
          {!loading && checklistData.items.length === 0 && (
            <div className="text-center py-12">
              <div className="mb-4">
                <ExpoLogo size="large" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Checklist Items Found</h3>
              <p className="text-gray-600">No checklist items found for Booth {boothNumber} in our system.</p>
              <p className="text-gray-500 text-sm mt-2">Managed by Expo Convention Contractors</p>
            </div>
          )}

          {/* Footer */}
          <div className="mt-12 text-center bg-white/90 backdrop-blur-lg rounded-2xl p-6 border border-gray-200 shadow-lg">
            <div className="flex items-center justify-center mb-3">
              <ExpoLogo size="large" />
            </div>
            <p className="text-gray-600 text-sm font-medium mb-2">
              "Large Enough To Be Exceptional, Yet Small Enough To Be Personable"
            </p>
            <p className="text-gray-500 text-xs">
              Expo Convention Contractors Inc. • Professional Exhibition Management • Miami, Florida
            </p>
            <div className="mt-4 text-xs text-gray-400">
              ExpoFlow v3.0 • Real-time Checklist Tracking System
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (stage === 'orders') {
    const deliveredOrders = orders.filter(o => o.status === 'delivered').length;
    const pendingOrders = orders.filter(o => o.status !== 'delivered' && o.status !== 'cancelled').length;

    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white p-6">
        <div className="max-w-7xl mx-auto">
          
          <div className="bg-white/90 backdrop-blur-lg rounded-3xl p-4 md:p-6 border border-gray-200 shadow-xl mb-8">
            <div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0">
              
              <div className="flex items-center space-x-3 md:space-x-6">
                <div className="flex items-center space-x-3 md:space-x-4">
                  <ExpoLogo size="small" />
                  <div className="w-12 h-12 md:w-16 md:h-16 rounded-2xl bg-gradient-to-br from-teal-600 to-teal-700 flex items-center justify-center shadow-lg border border-gray-300">
                    <Building2 className="w-6 h-6 md:w-8 md:h-8 text-white" />
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <h1 className="text-xl md:text-3xl font-bold text-gray-900">Booth {boothNumber}</h1>
                  <p className="text-sm md:text-base text-gray-600">
                    <span className="text-teal-600">Live Order Tracking</span>
                  </p>
                  <div className="flex flex-wrap items-center gap-2 md:gap-4 mt-1 md:mt-2">
                    <span className="text-xs md:text-sm text-teal-600 flex items-center space-x-1">
                      <Shield className="w-3 h-3 md:w-4 md:h-4" />
                      <span>Expo Convention Contractors</span>
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center justify-end space-x-2 md:space-x-4 flex-shrink-0">
                <button 
                  onClick={() => setStage('options')}
                  className="px-3 py-2 md:px-6 md:py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl md:rounded-2xl transition-all duration-300 border border-gray-200 text-sm md:text-base"
                >
                  ← Back
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white/90 backdrop-blur-lg rounded-2xl p-6 border border-gray-200 shadow-lg">
              <div className="flex items-center space-x-3 mb-4">
                <Package className="w-8 h-8 text-teal-600" />
                <h3 className="text-lg font-semibold text-gray-900">Total Orders</h3>
              </div>
              <div className="text-3xl font-bold text-teal-600">{orders.length}</div>
              <div className="text-xs text-gray-500 mt-1">Managed by Expo CCI</div>
            </div>
            <div className="bg-white/90 backdrop-blur-lg rounded-2xl p-6 border border-gray-200 shadow-lg">
              <div className="flex items-center space-x-3 mb-4">
                <CheckCircle className="w-8 h-8 text-green-500" />
                <h3 className="text-lg font-semibold text-gray-900">Delivered</h3>
              </div>
              <div className="text-3xl font-bold text-green-500">{deliveredOrders}</div>
              <div className="text-xs text-gray-500 mt-1">Completed</div>
            </div>
            <div className="bg-white/90 backdrop-blur-lg rounded-2xl p-6 border border-gray-200 shadow-lg">
              <div className="flex items-center space-x-3 mb-4">
                <Shield className="w-8 h-8 text-purple-500" />
                <h3 className="text-lg font-semibold text-gray-900">In Progress</h3>
              </div>
              <div className="text-3xl font-bold text-purple-500">{pendingOrders}</div>
              <div className="text-xs text-gray-500 mt-1">Live tracking</div>
            </div>
          </div>

          {loading && (
            <div className="text-center py-8">
              <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-700">Loading orders from Expo CCI Database...</p>
            </div>
          )}

          {notifications.length > 0 && (
            <div className="bg-white/90 backdrop-blur-lg rounded-2xl p-6 border border-gray-200 shadow-lg mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
                <Sparkles className="w-6 h-6 text-teal-600" />
                <span>Live Updates</span>
              </h2>
              <div className="space-y-3">
                {notifications.map((notif) => (
                  <div key={notif.id} className="flex items-center space-x-4 p-3 bg-gray-50 rounded-lg border border-gray-100">
                    <div className="w-2 h-2 bg-teal-500 rounded-full animate-pulse"></div>
                    <span className="text-gray-800 flex-1">{notif.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {orders.map((order) => {
              const statusInfo = orderStatuses[order.status] || orderStatuses['in-process'];
              const StatusIcon = statusInfo.icon;
              
              return (
                <div key={order.id} className="bg-white/90 backdrop-blur-lg rounded-2xl p-6 border border-gray-200 hover:border-gray-300 transition-all duration-300 shadow-lg">
                  
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <StatusIcon className="w-6 h-6 text-gray-700" />
                      <span className="text-gray-900 font-bold">{order.id}</span>
                    </div>
                    <span className="text-xs bg-teal-100 text-teal-700 px-2 py-1 rounded-full">
                      Expo CCI
                    </span>
                  </div>

                  <h3 className="text-xl font-bold text-gray-900 mb-2">{order.item}</h3>
                  <p className="text-gray-600 text-sm mb-4">{order.description}</p>

                  <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
                    <div>
                      <p className="text-gray-500">Order Date</p>
                      <p className="text-gray-900 font-medium">{order.order_date}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Quantity</p>
                      <p className="text-gray-900 font-medium">{order.quantity}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Color</p>
                      <p className="text-gray-900 font-medium">{order.color}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Section</p>
                      <p className="text-gray-900 font-medium">{order.section}</p>
                    </div>
                  </div>

                  <div className="mb-4">
                    {renderProgressBar(order.status)}
                  </div>

                  <div className={`inline-flex items-center space-x-2 px-3 py-2 rounded-full ${statusInfo.bgColor}`}>
                    <StatusIcon className="w-4 h-4" />
                    <span className="text-sm font-medium">{statusInfo.label}</span>
                  </div>

                  {order.comments && (
                    <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-100">
                      <p className="text-gray-500 text-xs mb-1">Comments</p>
                      <p className="text-gray-800 text-sm">{order.comments}</p>
                    </div>
                  )}

                  <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
                    <ExpoLogo size="small" />
                    <span className="text-xs text-gray-400">Managed by Expo Convention Contractors</span>
                  </div>
                </div>
              );
            })}
          </div>

          {!loading && orders.length === 0 && (
            <div className="text-center py-12">
              <div className="mb-4">
                <ExpoLogo size="large" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Orders Found</h3>
              <p className="text-gray-600">No orders found for Booth {boothNumber} in our system.</p>
              <p className="text-gray-500 text-sm mt-2">Managed by Expo Convention Contractors</p>
            </div>
          )}

          <div className="mt-12 text-center bg-white/90 backdrop-blur-lg rounded-2xl p-6 border border-gray-200 shadow-lg">
            <div className="flex items-center justify-center mb-3">
              <ExpoLogo size="large" />
            </div>
            <p className="text-gray-600 text-sm font-medium mb-2">
              "Large Enough To Be Exceptional, Yet Small Enough To Be Personable"
            </p>
            <p className="text-gray-500 text-xs">
              Expo Convention Contractors Inc. • Professional Exhibition Management • Miami, Florida
            </p>
            <div className="mt-4 text-xs text-gray-400">
              ExpoFlow v3.0 • Real-time Order Tracking System
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default App;
