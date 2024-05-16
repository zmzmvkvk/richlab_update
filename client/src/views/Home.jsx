import styles from "../css/Home.module.css";
import Card from "../components/Card";
import Login from "../components/Login";
import ShortCut from "../components/ShortCut";
import GenerateCsv from "../components/GenerateCsv";
import RandomKeyword from "../components/RandomKeyword";
import CommingSoon from "../components/CommingSoon";

const Home = () => {
  const totalCard = [
    { id: 1, title: "login", children: <Login></Login> },
    { id: 2, title: "shortcut-website", children: <ShortCut></ShortCut> },
    { id: 3, title: "generate-csv", children: <GenerateCsv></GenerateCsv> },
    {
      id: 4,
      title: "generate-random-keyword",
      children: <RandomKeyword></RandomKeyword>,
    },
    { id: 5, title: "comming-soon", children: <CommingSoon></CommingSoon> },
    { id: 6, title: "comming-soon", children: <CommingSoon></CommingSoon> },
    { id: 7, title: "comming-soon", children: <CommingSoon></CommingSoon> },
    { id: 8, title: "comming-soon", children: <CommingSoon></CommingSoon> },
    { id: 9, title: "comming-soon", children: <CommingSoon></CommingSoon> },
  ];
  return (
    <div className={styles.cardSection}>
      {totalCard.map((it, idx) => {
        return (
          <Card key={idx} id={it.title}>
            {it.children}
          </Card>
        );
      })}
    </div>
  );
};

export default Home;
