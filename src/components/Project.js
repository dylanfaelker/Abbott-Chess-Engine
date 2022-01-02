const Project = ({ project, onHover, onClick}) => {
    return (
        <div
            className='project' 
            onMouseEnter={() => onHover(project.id, false)} 
            onMouseLeave={() => onHover(project.id, true)}
            onClick={() => onClick(project.link)}
        >
            {project.display ? project.name : project.desc}
        </div>
    )
}

export default Project
