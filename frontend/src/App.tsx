import { useGameState } from "./hooks/useGameState";
import { useGameSocket } from "./hooks/useGameSocket";
import { Layout } from "./components/Layout";

function App() {
  const [state, dispatch] = useGameState();
  useGameSocket(dispatch);

  return <Layout state={state} />;
}

export default App;
