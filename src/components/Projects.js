import Project from './Project'

const Projects = ({ projects, onHover, onClick}) => {
    return (
        <div className='section'>
            <header className='header'>
                <h2>Projects</h2>
            </header>
            {projects.map((project) => (
                <Project
                    key={project.id} 
                    project={project}
                    onHover={onHover}
                    onClick={onClick}
                />
            ))}
        </div>
    )
}

export default Projects

