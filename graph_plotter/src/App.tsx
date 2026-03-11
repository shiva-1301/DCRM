import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { DataProvider } from './context/DataContext';
import { Layout } from './components/Layout';
import { EditModeDraggable } from './components/EditModeDraggable';

function App() {
  return (
    <DataProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />} />
          <Route path="/edit" element={<EditModeDraggable />} />
        </Routes>
      </BrowserRouter>
    </DataProvider>
  );
}

export default App;
