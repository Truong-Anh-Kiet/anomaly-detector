export default function Dashboard() {
  return (
    <div className="text-center py-12">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">
        Welcome to Anomaly Detection Dashboard
      </h2>
      <p className="text-gray-600 mb-8">
        Dashboard components will be implemented in Phase 3+
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-12">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Real-Time Alerts (US1)
          </h3>
          <p className="text-gray-600">
            View detected anomalies across all financial categories
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Time Series Charts (US2)
          </h3>
          <p className="text-gray-600">
            Visualize transaction history with anomalies highlighted
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Explainable Insights (US3)
          </h3>
          <p className="text-gray-600">
            Access detailed explanations for detected anomalies
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Advanced Filtering (US4)
          </h3>
          <p className="text-gray-600">
            Filter anomalies by date, category, severity, and type
          </p>
        </div>
      </div>
    </div>
  )
}
