import JaguarReIdPage from '@/components/JaguarReIdPage';
import { ThemeProvider } from '@/components/ThemeProvider';

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="wildtrack-theme">
      <JaguarReIdPage />
    </ThemeProvider>
  );
}

export default App;
