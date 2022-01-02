import { useState } from 'react'
import profile from './ProfileCircle.png';
import { ReactComponent as InstagramIcon } from './instagram.svg'
import { ReactComponent as GithubIcon } from './github.svg'
import { ReactComponent as EmailIcon } from './email.svg'
import { ReactComponent as LinkedinIcon } from './linkedin.svg'
import './App.css';
import Typer from './components/Typer'
import Projects from './components/Projects'
import Contacts from './components/Contacts'
import Game from './Game'
import Game_engine from './Game_engine'
import Navbar from './components/Navbar'
import Project from './components/Project'
import Contact from './components/Contact'
import Careers from './components/Careers'

function App() {
  const [projects, setProjects] = useState([   
    {
      id: 1,
      name: <h3>Infinity Chess</h3>,
      desc: <div>
              <p className='paragraph'>A game which extends upon the traditional chess experience by adding a feature where the edges of the board wrap. Basically a combination of Pacman and Chess. I am current working on a simple engine so it can be played on this website.</p>
              <p className='paragraph'>Languages and Libraries: React.js</p>
            </div>,
      display: true,
      link: 2,
    },
    {
      id: 2,
      name: <h3>Stock Porfolio Creater</h3>,
      desc: <div>
              <p className='paragraph'>Creates an investment portfolio of ten SP500 stocks that is considered risky. It uses data analytics with panda's and numpy so ensure a risky portfolio is chosen.</p>
              <p className='paragraph'>Languages and Libraries: Python, Numpy, Pandas, YFinance</p>
            </div>,
      display: true,
      link: 0,
    },
    {
      id: 3,
      name: <h3>FEN Decoder</h3>,
      desc: <div>
              <p className='paragraph'>FEN (Forsyth–Edwards Notation) is a chess notation used by computer to easily understand a position. To humans, it can be difficult to quickly recognized what is happening. This program parses the FEN chess notation into visualisation a board.</p>
              <p className='paragraph'>Languages and Libraries: Java</p>
            </div>,
      display: true,
      link: 'https://github.com/dylpykill/FENDecoder'
    },
    {
      id: 4,
      name: <h3>Santa's Elf (Incomplete)</h3>,
      desc: <div>
              <p className='paragraph'>A discord bot that will organise secret Santa without the need for a human organiser making it quicker and easier to arrange.</p>
              <p className='paragraph'>Languages and Libraries: Python, Discord Bot API</p>
            </div>,
      display: true,
      link: 'https://github.com/dylpykill/Santa-s-Elf'
    },
    {
      id: 5,
      name: <h3>Personal Website (Incomplete)</h3>,
      desc: <div>
              <p className='paragraph'>What you are currently looking at.</p>
              <p className='paragraph'>Languages and Libraries: React.js</p>
            </div>,
      display: true,
      link: 'https://github.com/dylpykill/PersonalWebsite'
    }
  ])

  const [contacts, setContacts] = useState([
    {
      id: 1,
      icon: <InstagramIcon style={{fill:'#366BA8'}}/>,
      iconHighlight: <InstagramIcon style={{fill:'#42afb0'}}/>,
      writting: <p className='contact'>@d_faelker</p>,
      link: "https://www.instagram.com/d_faelker/?hl=en"
    },
    {
      id: 2,
      icon: <GithubIcon style={{fill:'#366BA8'}}/>,
      iconHighlight: <GithubIcon style={{fill:'#42afb0'}}/>,
      writting: <p className='contact'>Dylan Faelker</p>,
      link: "mailto:faelkerd@gmail.com"
    },
    {
      id: 3,
      icon: <EmailIcon style={{fill:'#366BA8'}}/>,
      iconHighlight: <EmailIcon style={{fill:'#42afb0'}}/>,
      writting: <p className='contact'>faelkerd@gmail.com</p>,
      link: "https://github.com/dylpykill"
    },
    {
      id: 4,
      icon: <LinkedinIcon style={{fill:'#366BA8'}}/>,
      iconHighlight: <LinkedinIcon style={{fill:'#42afb0'}}/>,
      writting: <p className='contact'>Dylan Faelker</p>,
      link: "https://www.linkedin.com/in/dylanfaelker/"
    },
  ])

  const [navs, setNavs] = useState([
    {
      id:1,
      name:<h3>Home</h3>,
      link:0,
    },
    {
      id:2,
      name:<h3>About</h3>,
      link:1,
    },
    {
      id:3,
      name:<h3>Infinity Chess</h3>,
      link:2,
    }
  ])

  const [careers, setCareers] = useState([
    {
      id: 1,
      title: <p className='job-title'>First Co-op Placement</p>,
      location: <p className='job-location'>Unknown</p>,
      date: <p className='job-period'>––– May 2022 - August 2022</p>,
    },
    {
      id: 2,
      title: <p className='job-title'>Lifeguard and Swim Instructor</p>,
      location: <p className='job-location'>Town of Oakville</p>,
      date: <p className='job-period'>––– September 2019 - September 2021</p>,
    },
    {
      id: 3,
      title: <p className='job-title'>Slide Attendant and Cashier</p>,
      location: <p className='job-location'>Town of Oakville</p>,
      date: <p className='job-period'>––– September 2018 - September 2019</p>,
    },
    {
      id: 4,
      title: <p className='job-title'>Soccer Referee</p>,
      location: <p className='job-location'>Oakville Soccer Club</p>,
      date: <p className='job-period'>––– June 2018 - August 2018</p>,
    },
  ])

  //0=home, 1=about, 2=infinitychess, 3=infinitychess(engine)
  const [pageNum, setPageNum] = useState(0)

  //Show description
  const showDesc = (id, display) => (
    setProjects(
      projects.map((project) => 
        project.id === id ? 
          {...project, display:display} : 
          project
      )
    )
  )

  const highlightContact =  (id, hover) => (
    setContacts(
      contacts.map((contact) => 
        contact.id === id ? 
          {...contact, hover:hover} : 
          contact
      )
    )
  )

  const highlightNav =  (id, hover) => (
    setNavs(
      navs.map((nav) => 
        nav.id === id ? 
          {...nav, hover:hover} : 
          nav
      )
    )
  )



  //opens a link in a new tab or changes pageNum
  const openInNewTab = (url) => {
    if(isNaN(url)) {
      const newWindow = window.open(url, '_blank', 'noopener,noreferrer')
      if (newWindow) newWindow.opener = null
    }
    else {
      setPageNum(url)
    }
  }

  return (
    <div>
      <Navbar navs={navs} onHover={highlightNav} onClick={openInNewTab} />
      {pageNum === 0 ?
        <div className="App">
          <header className='wrapper'>
            <img src={profile} className="App-logo" alt="logo"/>
            <header className='App-header'>
              <h1 >
                Dylan Faelker
              </h1>
              <h4 style={{color: 'rgb(207,188,94)'}}>
                I am a
                Sofware Developer,
                CFM student at UWaterloo,
                Runner and
                Amateur Investor
              </h4>
              {/* <h4>
                I am a 
                <Typer 
                  cycleWords={['Software Developer',
                              'CFM student at UWaterloo',
                              'Amature investor', 
                              'Runner']}
                />
              </h4> */}
            </header>
          </header>

          <Projects 
            projects={projects}
            onHover={showDesc}
            onClick={openInNewTab}
          />

          <Contacts 
            contacts={contacts}
            onHover={highlightContact}
          />
        </div> :
        (pageNum===1 ? 

          // ************* About Page ****************
          <div className='App'>

            <header className='header'>
              <h2>About Me</h2>
            </header>

            {/* About Me */}
            <div className='section'>
              <p className='description'>
                I am currently taking my undergraduate degree at Waterloo for Computing and Financial Management (BCFM).
                The program is similar to a double major in Computer Science and Finance.
                I chose these fields because in high school, I really enjoyed analysing a company in grade 12 accounting and I liked the problem solving in computer science.
                I am also inspired by the growth of fintech and look forawrd to oppertunities to bring my knowledge of computing and financial management to use.
              </p>
            </div>

            {/* Hobbies */}
            <div className='section'>
              <header className='header'>
                <h3>Hobbies</h3>
              </header>
              <p className='description'>
                Running has always been important to me. In grade 3, I joined the cross country team and continued with the sport all the way until grade 12 where it was canceled due to COVID.
                In grade 9, I started taking it seriously when I signed up for my first race with my mom. It was a 10km and I came 3rd in my age group.
                In grade 10, I trained throughout the summer for cross country in the fall and secured my placement at OFSAA which is something I am still proud of.
                I took a break for a while but once COVID hit, I used running as something to do and ran over 1000 miles in 2020. 
              </p>
              <p className='description'>
                In the first summer of the pandmeic, I started road biking with a couple big goals in mind. The first two were biking to the CN Tower in Toronto and back (100km), something I have now done 3 times, and biking to Niagara Falls and back (200km).
              </p>
              <p className='description'>
                My final goal was a half Ironman. I had planned to try one in the summer of 2021 but COVID had other plans. I still hope to do one soon, and eventually complete even a full Ironman.
              </p>
            </div>

            {/* Career History */}
            <Careers careers={careers}/>
          </div> :
          (pageNum==2 ?

          // ************* Page with infinity chess ****************
          <div className='App'>

            <header className='header'>
              <h2>Infinity Chess</h2>
            </header>

            <Game />

            {/* Descriptions and writting about infinity chess */}
            <div className='section'>

              {/* Rules */}
              <header className='header'>
                <h3>Rules</h3>
              </header>
              <p className='description'>
                Pieces all move that same as normal chess including enpassent and castling. The only change is, like Pacman, if you go off one side of the board, you will appear on the other.
                This only applies to the files. You cannot go from the first rank to the eigth rank since white would win on the first move. 
              </p>
              <p className='description'>
                For example, if a rook was on a1 and there was a bishop on c1, the rook could get to d1 by sliding off the left side of the board, appearing on the right, and continuing to d1.
                It may be helpful to think of it as there being 3 of the exact same boards laid beside eachother. If the white queen from the middle board sees the black king on the right board, black is in check.
              </p>

              {/* About */}
              <header className='header'>
                <h3>About</h3>
              </header>
              <p className='description'>
                In 2020, the world was hit with a pandemic leaving many people at home. During this time people looked for things to do. Due to this, and the hit Netflix series 'The Queen's Gambit', many started playing chess.
                My friends and I were part of this group and after a few months of playing, my friend Richard He appraoched me with the idea for this game which combines Pacman and Chess. 
              </p>
              <p className='description'>
                There is a similar variant to chess called infinite chess where the board is unbounded in all directions, but the board never wraps and that's where the difference lies.
              </p>
              <p className='description'>
                I was originally learning Java at the time and tried to create it in that language but after a couple bugs and not enough patience to understand how to make proper graphics, I gave up.
              </p>
              <p className='description'>
                About a month later, I entered into a hackathon and decided to give the idea another try, but in python and starting out with a half completed chess game. This didn't go very well as the original chess game did not have any of the more complicated rules of chess and it has a bug where it becomes unplayable after about 20 moves.
              </p>
              <p className='description'>
                I eventually decided to give it another go in React.js since I was working on resumes and a personal website when I realised I did not have many interesting side projects. I was already using React.js for my website and it seemed a lot easier to get working. I have since finished this project and I'm now working on a bot.
              </p>
            </div>

            {/* Link to Engine version */}
            <div className='section'>
              <Project
                key={1} 
                project={{ display:true, name:<h3>Infinity Chess (Engine)</h3>, link:3  }}
                // onHover={onHover}
                onClick={openInNewTab}
              />
            </div>

            {/* Link to Git hub */}
            <div className='section'>
              <header className='header'>
                <h4>Github page</h4>
              </header>
              <Contact 
                contact={{
                  id: 1,
                  icon: <GithubIcon style={{fill:'#366BA8'}}/>,
                  writting: <p className='link-to-github'>Infinity-Chess Github</p>,
                  link: "https://github.com/dylpykill/Infinity-Chess"
                }}
              />
            </div>
            
          </div> :

          // ************* Page with infinity chess and engine ****************
          <div className='App'>

            <header className='header'>
              <h2>Infinity Chess vs Abbott V1.0</h2>
            </header>

            <Game_engine />

            {/* Descriptions and writting about infinity chess */}
            <div className='section'>

              {/* About */}
              <header className='header'>
                <h3>About the Engine</h3>
              </header>
              <p className='description'>
                This engine (Abbott) is very simple and probably rated about 500-600. It can only see one move into the future (1 move for white, 1 move for black) and evaluates positions based on material, king safety and control of squares. I did not put too much effort into the engine since I didn't have enough time to commit to it, but I still wanted have something to play against, and so we have this.
              </p>
              <p className='description'>
                There is one line where it gets mated in 6 moves everytime. (1. e4 f6  2. c4+ h5  3. Be2 Kf7  4. Bxh5+ Rxh5  5. Qxh5+ Ke6  6. Qd5#)
              </p>
              <p className='description'>
                This is only version 1 (V1) and I plan to develope it futher in the future to include more evaluation features to help in endgames and position of pieces, as well as some efficiency techniques like alpha beta pruning that will allow it to look further into the future. When I do so, I will likely do so in another language and restructure many of the data types. 
              </p>
              <p className='description'>
                For now though, this is the only engine for Infinity Chess.
              </p>

              {/* History */}
              <header className='header'>
                <h3>History of Abbott</h3>
              </header>
              <div className='career'>
                <p className='job-period'>––– Abbott V1.0</p>
                <p className='job-title'>Jan 2021</p>
                <p className='job-location'>Rating: ~500</p>
                <p className='job-location'>Max depth: 1</p>
            </div>
            </div>

            {/* Link to Git hub */}
            <div className='section'>
              <header className='header'>
                <h4>Github page</h4>
              </header>
              <Contact 
                contact={{
                  id: 1,
                  icon: <GithubIcon style={{fill:'#366BA8'}}/>,
                  writting: <p className='link-to-github'>Abbott Github</p>,
                  link: "https://github.com/dylpykill/Infinity-Chess-Engine"
                }}
              />
            </div>
            
          </div>
          )
        )
      }
    </div>
  );
}

export default App;
