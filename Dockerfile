FROM osrf/ros:jazzy-desktop-full
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
    build-essential \
    cmake \
    git \
    vim \
    usbutils \
    x11-apps \
    libcanberra-gtk-module \
    libcanberra-gtk3-module

ARG UID=1000
ARG GID=1000
ARG USERNAME=developer

RUN userdel -r ubuntu && \
		groupadd -g ${GID} ${USERNAME} && \
    useradd -m -u ${UID} -g ${GID} -s /bin/bash ${USERNAME} && \
		echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} && \
		chmod 0440 /etc/sudoers.d/${USERNAME}

USER ${USERNAME}
WORKDIR /home/${USERNAME}/mirsws


RUN echo "source /opt/ros/jazzy/setup.bash" >> /home/${USERNAME}/.bashrc && \
    echo 'export PS1="\[\e[32m\]\u@mirs-sim\[\e[m\]:\[\e[34m\]\w\[\e[m\]\\$ "' >> /home/${USERNAME}/.bashrc && \
    echo "alias cb='colcon build --symlink-install'" >> /home/${USERNAME}/.bashrc && \
    echo "alias cbs='colcon build --symlink-install --packages-select'" >> /home/${USERNAME}/.bashrc && \
    echo "alias cbt='colcon build --symlink-install --packages-up-to'" >> /home/${USERNAME}/.bashrc && \
    echo "alias ru='rosdep update'" >> /home/${USERNAME}/.bashrc && \
    echo "alias ri='rosdep install --from-path src --ignore-src -r -y'" >> /home/${USERNAME}/.bashrc && \
    echo "alias si='source install/setup.bash'" >> /home/${USERNAME}/.bashrc && \
    echo "alias mirs='ros2 launch mirs mirs.launch.py'" >> /home/${USERNAME}/.bashrc && \
    echo "alias slam='ros2 launch mirs slam.launch.py'" >> /home/${USERNAME}/.bashrc && \
    echo "alias nav='ros2 launch mirs nav.launch.py'" >> /home/${USERNAME}/.bashrc

CMD ["bash"]
