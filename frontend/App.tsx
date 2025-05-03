import './App.css'

import { createBrowserRouter, RouterProvider } from 'react-router-dom'

import HomePage from './pages/Dashboard'
import RootLayout from './pages/RootLayout'
import SurveillancePage from './pages/Surveillance'
import View3DPage from './pages/View3D'
import { useEffect, useRef } from 'react'
import { useDispatch } from 'react-redux'
import { webSocketActions } from './store/webSocketSlice'
import ErrorPage from './pages/ErrorPage'

const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    errorElement: <ErrorPage />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'surveillance',
        element: <SurveillancePage />,
      },
      {
        path: 'three-dimensional-view',
        element: <View3DPage />
      }
    ]
  }
]);

function App() {
  const socket = useRef<WebSocket>(null);
  const dispatch = useDispatch();

  useEffect(() => {
    socket.current = new WebSocket('ws://localhost:8765');
    if (socket.current) {
      socket.current.onmessage = e => {
        dispatch(webSocketActions.setScatter(JSON.parse(e.data).scatter));
      };
    }
    return () => socket.current?.close();
  }, []);

  // useEffect(() => {
  // }, [socket.current]);

  return (
    <>
      <RouterProvider router={router} />
    </>
  )
}

export default App
